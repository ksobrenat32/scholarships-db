from django.core import mail as django_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator as token_gen
import os
import smtplib
import django
from unittest.mock import patch
from packaging.version import parse
from django.conf import settings
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from becas_sntsa.models import (
    Becario, Trabajador, Seccion, Puesto, Jurisdiccion, LugarAdscripcion,
    Grado, SolicitudAprovechamiento, SolicitudExcelencia, SolicitudEspecial,
)
from becas_sntsa.forms import (
    validar_curp, BecarioCreateForm, BecarioEditForm,
    SolicitudAprovechamientoCreateForm, SolicitudExcelenciaCreateForm,
    SolicitudEspecialCreateForm,
)
from django.core.files.uploadedfile import SimpleUploadedFile


class BecarioModelTest(TestCase):

    def test_get_sexo(self):
        """
        Tests the get_sexo method of the Becario model.
        """
        becario_h = Becario(curp="SAHM910101HDFLNAA1")
        becario_m = Becario(curp="SAHM910101MDFLNAA1")
        self.assertEqual(becario_h.get_sexo(), 'H')
        self.assertEqual(becario_m.get_sexo(), 'M')

    def test_get_fecha_nacimiento(self):
        """
        Tests the get_fecha_nacimiento method of the Becario model.
        """
        # Test case for a birth year in the 20th century
        becario_1991 = Becario(curp="SAHM910101HDFLNAA1")
        self.assertEqual(becario_1991.get_fecha_nacimiento(), "1991-01-01")

        # Test case for a birth year in the 21st century
        becario_2005 = Becario(curp="SAHM050101HDFLNAA1")
        self.assertEqual(becario_2005.get_fecha_nacimiento(), "2005-01-01")


class AuthViewsTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='SAHM910101HDFLNAA1', password='testpassword')

    def test_signup_view_get(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'signup.html')

    def test_signup_view_post_success(self):
        response = self.client.post(reverse('signup'), {
            'username': 'SAHM910101HDFLNAA2',
            'password1': 'newpassword',
            'password2': 'newpassword'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            User.objects.filter(
                username='SAHM910101HDFLNAA2').exists())

    def test_signup_view_post_password_mismatch(self):
        response = self.client.post(reverse('signup'), {
            'username': 'SAHM910101HDFLNAA3',
            'password1': 'newpassword',
            'password2': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Las contraseñas no coinciden')

    def test_signup_view_post_invalid_curp(self):
        response = self.client.post(reverse('signup'), {
            'username': 'INVALIDCURP',
            'password1': 'newpassword',
            'password2': 'newpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Formato de CURP inválido')

    def test_signin_view_get(self):
        response = self.client.get(reverse('signin'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'signin.html')

    def test_signin_view_post_success(self):
        response = self.client.post(reverse('signin'), {
            'username': 'SAHM910101HDFLNAA1',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('becas'))

    def test_signin_view_post_fail(self):
        response = self.client.post(reverse('signin'), {
            'username': 'SAHM910101HDFLNAA1',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Usuario o contraseña inválidos')

    def test_signout_view(self):
        self.client.login(
            username='SAHM910101HDFLNAA1',
            password='testpassword')
        response = self.client.get(reverse('signout'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('home'))


class AccessControlTest(TestCase):
    def setUp(self):
        # Create related objects for Trabajador
        self.seccion = Seccion.objects.create(numero=1)
        self.puesto = Puesto.objects.create(clave='P1')
        self.jurisdiccion = Jurisdiccion.objects.create(clave='J1')
        self.lugar = LugarAdscripcion.objects.create(nombre='Lugar 1')

        # A user without a trabajador profile
        self.no_trabajador_user = User.objects.create_user(
            username='SAHM910101HDFLNAA2', password='testpassword')

        # A user with a non-approved trabajador profile
        self.unapproved_user = User.objects.create_user(
            username='SAHM910101HDFLNAA3', password='testpassword')
        self.unapproved_trabajador = Trabajador.objects.create(
            usuario=self.unapproved_user,
            nombre='Test',
            apellido_paterno='User',
            talon_pago_archivo=SimpleUploadedFile("file.txt", b"file_content"),
            telefono='1234567890',
            correo='test@test.com',
            seccion=self.seccion,
            puesto=self.puesto,
            jurisdiccion=self.jurisdiccion,
            lugar_adscripcion=self.lugar,
            aprobado=False
        )

        # A user with an approved trabajador profile
        self.approved_user = User.objects.create_user(
            username='SAHM910101HDFLNAA4', password='testpassword')
        self.approved_trabajador = Trabajador.objects.create(
            usuario=self.approved_user,
            nombre='Approved',
            apellido_paterno='User',
            talon_pago_archivo=SimpleUploadedFile("file.txt", b"file_content"),
            telefono='1234567890',
            correo='approved@test.com',
            seccion=self.seccion,
            puesto=self.puesto,
            jurisdiccion=self.jurisdiccion,
            lugar_adscripcion=self.lugar,
            aprobado=True
        )

    def test_trabajador_required_decorator_no_trabajador(self):
        """
        Test that a user without a trabajador profile is redirected to create_trabajador.
        """
        self.client.login(
            username='SAHM910101HDFLNAA2',
            password='testpassword')
        response = self.client.get(reverse('becas'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('create_trabajador'))

    def test_trabajador_required_decorator_with_trabajador(self):
        """
        Test that a user with a trabajador profile can access the view.
        """
        self.client.login(
            username='SAHM910101HDFLNAA3',
            password='testpassword')
        response = self.client.get(reverse('becas'))
        self.assertEqual(response.status_code, 200)

    def test_approved_required_decorator_not_approved(self):
        """
        Test that a user with a non-approved trabajador is shown the 'espera_verificacion' page.
        """
        self.client.login(
            username='SAHM910101HDFLNAA3',
            password='testpassword')
        response = self.client.get(reverse('create_becario'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'espera_verificacion.html')

    def test_approved_required_decorator_is_approved(self):
        """
        Test that a user with an approved trabajador can access the view.
        """
        self.client.login(
            username='SAHM910101HDFLNAA4',
            password='testpassword')
        response = self.client.get(reverse('create_becario'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_becario.html')

    def test_login_required_for_decorated_views(self):
        """
        Test that an unauthenticated user is redirected to the login page.
        """
        response = self.client.get(reverse('becas'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('signin'), response.url)

        response = self.client.get(reverse('create_becario'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('signin'), response.url)


class CreationViewsTest(TestCase):
    def setUp(self):
        self.seccion = Seccion.objects.create(numero=1)
        self.puesto = Puesto.objects.create(clave='P1')
        self.jurisdiccion = Jurisdiccion.objects.create(clave='J1')
        self.lugar = LugarAdscripcion.objects.create(nombre='Lugar 1')
        self.grado = Grado.objects.create(clave='G1', nombre='Grado 1')

        self.user = User.objects.create_user(
            username='SAHM910101HDFLNAA5', password='testpassword')
        self.trabajador = Trabajador.objects.create(
            usuario=self.user,
            nombre='Test',
            apellido_paterno='User',
            talon_pago_archivo=SimpleUploadedFile("file.txt", b"file_content"),
            telefono='1234567890',
            correo='test@test.com',
            seccion=self.seccion,
            puesto=self.puesto,
            jurisdiccion=self.jurisdiccion,
            lugar_adscripcion=self.lugar,
            aprobado=True
        )
        self.client.login(
            username='SAHM910101HDFLNAA5',
            password='testpassword')

    def test_create_trabajador_view_get(self):
        # This user already has a trabajador, so it should not show the page, but redirect.
        # But the view does not check if a trabajador already exists.
        # It's a bug in the view, but the test will reflect the current
        # behavior.
        response = self.client.get(reverse('create_trabajador'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_trabajador.html')

        # A new user without trabajador
        user2 = User.objects.create_user(  # noqa: F841
            username='SAHM910101HDFLNAA6',
            password='testpassword')
        self.client.login(
            username='SAHM910101HDFLNAA6',
            password='testpassword')
        response = self.client.get(reverse('create_trabajador'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_trabajador.html')

    def test_create_trabajador_view_post(self):
        user2 = User.objects.create_user(
            username='SAHM910101HDFLNAA7',
            password='testpassword')
        self.client.login(
            username='SAHM910101HDFLNAA7',
            password='testpassword')

        data = {
            'nombre': 'New',
            'apellido_paterno': 'Trabajador',
            'telefono': '1112223333',
            'correo': 'new@test.com',
            'seccion': self.seccion.id,
            'puesto': self.puesto.id,
            'jurisdiccion': self.jurisdiccion.id,
            'lugar_adscripcion': self.lugar.id,
            'talon_pago_archivo': SimpleUploadedFile(
                "file.txt",
                b"file_content")}
        response = self.client.post(
            reverse('create_trabajador'), data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Trabajador.objects.filter(usuario=user2).exists())

    def test_create_becario_view_post(self):
        data = {
            'nombre': 'New',
            'apellido_paterno': 'Becario',
            'curp': 'SAHM050101HDFLNAA2',
            'curp_archivo': SimpleUploadedFile("curp.txt", b"file_content"),
            'acta_nacimiento': SimpleUploadedFile("acta.txt", b"file_content")
        }
        response = self.client.post(
            reverse('create_becario'), data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Becario.objects.filter(
                curp='SAHM050101HDFLNAA2').exists())

    def test_create_solicitud_aprovechamiento_view_post(self):
        becario = Becario.objects.create(
            trabajador=self.user,
            nombre='Test',
            apellido_paterno='Becario',
            curp='SAHM050101HDFLNAA3',
            curp_archivo=SimpleUploadedFile("curp.txt", b"file_content"),
            acta_nacimiento=SimpleUploadedFile("acta.txt", b"file_content")
        )
        data = {
            'becario': becario.id,
            'grado': self.grado.id,
            'promedio': 9.5,
            'boleta': SimpleUploadedFile("boleta.txt", b"file_content"),
            'recibo_nomina': SimpleUploadedFile("recibo.txt", b"file_content"),
            'ine': SimpleUploadedFile("ine.txt", b"file_content")
        }
        response = self.client.post(
            reverse('create_solicitud_aprovechamiento'), data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            SolicitudAprovechamiento.objects.filter(
                becario=becario).exists())

    def test_duplicate_solicitud_is_rejected(self):
        becario = Becario.objects.create(
            trabajador=self.user,
            nombre='Test',
            apellido_paterno='Becario',
            curp='SAHM050101HDFLNAA4',
            curp_archivo=SimpleUploadedFile("curp.txt", b"file_content"),
            acta_nacimiento=SimpleUploadedFile("acta.txt", b"file_content")
        )
        # Create one solicitud
        SolicitudAprovechamiento.objects.create(
            becario=becario,
            grado=self.grado,
            promedio=9.0,
            boleta=SimpleUploadedFile("boleta.txt", b"file_content"),
            recibo_nomina=SimpleUploadedFile("recibo.txt", b"file_content"),
            ine=SimpleUploadedFile("ine.txt", b"file_content"),
            estado='R'
        )

        data = {
            'becario': becario.id,
            'grado': self.grado.id,
            'promedio': 9.5,
            'boleta': SimpleUploadedFile(
                "boleta2.txt",
                b"file_content"),
            'recibo_nomina': SimpleUploadedFile(
                "recibo2.txt",
                b"file_content"),
            'ine': SimpleUploadedFile(
                "ine2.txt",
                b"file_content")}
        response = self.client.post(
            reverse('create_solicitud_aprovechamiento'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'El becario ya tiene una solicitud pendiente en esta categoría.')


class DownloadFileViewTest(TestCase):
    def setUp(self):
        self.seccion = Seccion.objects.create(numero=1)
        self.puesto = Puesto.objects.create(clave='P1')
        self.jurisdiccion = Jurisdiccion.objects.create(clave='J1')
        self.lugar = LugarAdscripcion.objects.create(nombre='Lugar 1')

        # Non-staff user
        self.non_staff_user = User.objects.create_user(
            username='nonstaff', password='testpassword')

        # Non-staff user 2
        self.non_staff_user2 = User.objects.create_user(
            username='nonstaff2', password='testpassword')

        # Staff user
        self.staff_user = User.objects.create_user(
            username='staff', password='testpassword', is_staff=True)

        # Create a file to download
        self.file = SimpleUploadedFile("test_file.txt", b"file content")
        self.trabajador = Trabajador.objects.create(
            usuario=self.non_staff_user,
            nombre='Test',
            apellido_paterno='User',
            talon_pago_archivo=self.file,
            telefono='1234567890',
            correo='test@test.com',
            seccion=self.seccion,
            puesto=self.puesto,
            jurisdiccion=self.jurisdiccion,
            lugar_adscripcion=self.lugar,
            aprobado=True
        )

    def test_download_file_non_staff_allowed(self):
        self.client.login(username='nonstaff', password='testpassword')
        response = self.client.get(
            reverse(
                'download_file', args=[
                    self.trabajador.talon_pago_archivo.name]))
        self.assertEqual(response.status_code, 200)

    def test_download_file_non_staff_forbidden(self):
        self.client.login(username='nonstaff2', password='testpassword')
        response = self.client.get(
            reverse(
                'download_file', args=[
                    self.trabajador.talon_pago_archivo.name]))
        self.assertEqual(response.status_code, 403)

    def test_download_file_staff(self):
        self.client.login(username='staff', password='testpassword')
        response = self.client.get(
            reverse(
                'download_file', args=[
                    self.trabajador.talon_pago_archivo.name]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.getvalue(), b"file content")

    def test_download_file_not_found(self):
        self.client.login(username='staff', password='testpassword')
        response = self.client.get(
            reverse(
                'download_file',
                args=['nonexistent_file.txt']))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "File not found.", status_code=403)

    def test_download_file_path_traversal(self):
        self.client.login(username='staff', password='testpassword')
        response = self.client.get(
            reverse(
                'download_file',
                args=['../../../../etc/passwd']))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Invalid file path.", status_code=403)

    def tearDown(self):
        # Clean up the created file
        file_path = os.path.join(
            settings.MEDIA_ROOT,
            self.trabajador.talon_pago_archivo.name)
        if os.path.exists(file_path):
            os.remove(file_path)


class DjangoVersionTest(TestCase):
    def test_django_version(self):
        """
        Tests that the Django version is at least 5.2.6.
        """
        self.assertTrue(parse(django.get_version()) >= parse('5.2.6'))


class PasswordChangeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_pass_user', password='oldpassword')

    def test_change_password_success(self):
        """
        Test that a logged-in user can change their password and is redirected to signin.
        """
        self.client.login(username='test_pass_user', password='oldpassword')
        response = self.client.post(reverse('change_password'), {
            'old_password': 'oldpassword',
            'new_password1': 'Newpassword_123',
            'new_password2': 'Newpassword_123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('signin'))

        # Verify the new password works
        auth_success = self.client.login(
            username='test_pass_user',
            password='Newpassword_123')
        self.assertTrue(auth_success)


class TrabajadorNotificationEmailTest(TestCase):
    def setUp(self):
        self.seccion = Seccion.objects.create(numero=1)
        self.puesto = Puesto.objects.create(clave='P1')
        self.jurisdiccion = Jurisdiccion.objects.create(clave='J1')
        self.lugar = LugarAdscripcion.objects.create(nombre='Lugar 1')
        self.user = User.objects.create_user(
            username='mail_notify_user',
            password='testpassword'
        )
        self.trabajador = Trabajador.objects.create(
            usuario=self.user,
            nombre='Test',
            apellido_paterno='Worker',
            talon_pago_archivo=SimpleUploadedFile("file.txt", b"file_content"),
            telefono='1234567890',
            correo='notify@test.com',
            seccion=self.seccion,
            puesto=self.puesto,
            jurisdiccion=self.jurisdiccion,
            lugar_adscripcion=self.lugar,
            aprobado=False
        )

    @patch('becas_sntsa.models.EmailMessage.send',
           side_effect=smtplib.SMTPException('smtp failure'))
    def test_aprobado_transition_does_not_fail_when_email_send_errors(
            self, mock_send):
        self.trabajador.aprobado = True
        with self.captureOnCommitCallbacks(execute=True):
            self.trabajador.save()
        self.trabajador.refresh_from_db()
        self.assertTrue(self.trabajador.aprobado)
        self.assertEqual(mock_send.call_count, 1)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class EmailVerificationViewTest(TestCase):
    def setUp(self):
        self.seccion = Seccion.objects.create(numero=1)
        self.puesto = Puesto.objects.create(clave='P1')
        self.jurisdiccion = Jurisdiccion.objects.create(clave='J1')
        self.lugar = LugarAdscripcion.objects.create(nombre='Lugar 1')

        self.user = User.objects.create_user(
            username='SAHM910101HDFLNAA9',
            password='testpassword',
            is_active=True,
        )
        self.trabajador = Trabajador.objects.create(
            usuario=self.user,
            nombre='Email',
            apellido_paterno='Verify',
            talon_pago_archivo=SimpleUploadedFile("f.txt", b"x"),
            telefono='1234567890',
            correo='verify@test.com',
            seccion=self.seccion,
            puesto=self.puesto,
            jurisdiccion=self.jurisdiccion,
            lugar_adscripcion=self.lugar,
            aprobado=True,
        )

    def test_activate_sets_user_active(self):
        """User starts inactive; hitting activate endpoint sets is_active=True."""
        self.user.is_active = False
        self.user.save()

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = token_gen.make_token(self.user)
        response = self.client.get(reverse('activate', args=[uid, token]))
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_activate_invalid_token_returns_error(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.get(
            reverse(
                'activate', args=[
                    uid, 'invalid-token']))
        self.assertEqual(response.status_code, 200)
        self.assertIn('inválido', response.content.decode())

    def test_confirm_email_change_updates_email(self):
        """confirm_email_change uses pending_email from DB to update User and Trabajador."""
        new_email = 'newemail@test.com'
        self.trabajador.pending_email = new_email
        self.trabajador.save()

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = token_gen.make_token(self.user)
        response = self.client.get(
            reverse(
                'confirm_email_change',
                args=[
                    uid,
                    token]))
        self.assertEqual(response.status_code, 200)

        self.user.refresh_from_db()
        self.trabajador.refresh_from_db()
        self.assertEqual(self.user.email, new_email)
        self.assertEqual(self.trabajador.correo, new_email)
        self.assertIsNone(self.trabajador.pending_email)

    def test_confirm_email_change_no_pending_email_returns_error(self):
        """confirm_email_change returns an error when no pending_email is set."""
        self.trabajador.pending_email = None
        self.trabajador.save()

        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = token_gen.make_token(self.user)
        response = self.client.get(
            reverse(
                'confirm_email_change',
                args=[
                    uid,
                    token]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('pendiente', response.content.decode())

    def test_confirm_email_change_invalid_token_returns_error(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.get(
            reverse(
                'confirm_email_change',
                args=[
                    uid,
                    'bad-token']))
        self.assertEqual(response.status_code, 200)
        self.assertIn('inválido', response.content.decode())


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class NotificationEmailOutboxTest(TestCase):
    def setUp(self):
        self.seccion = Seccion.objects.create(numero=1)
        self.puesto = Puesto.objects.create(clave='P1')
        self.jurisdiccion = Jurisdiccion.objects.create(clave='J1')
        self.lugar = LugarAdscripcion.objects.create(nombre='Lugar 1')
        self.grado = Grado.objects.create(clave='G1', nombre='Grado 1')

        self.user = User.objects.create_user(
            username='SAHM910101HDFLNAAB',
            password='testpassword',
        )
        self.trabajador = Trabajador.objects.create(
            usuario=self.user,
            nombre='Notif',
            apellido_paterno='Test',
            talon_pago_archivo=SimpleUploadedFile("f.txt", b"x"),
            telefono='1234567890',
            correo='notif@test.com',
            seccion=self.seccion,
            puesto=self.puesto,
            jurisdiccion=self.jurisdiccion,
            lugar_adscripcion=self.lugar,
            aprobado=False,
        )
        self.becario = Becario.objects.create(
            trabajador=self.user,
            nombre='Becario',
            apellido_paterno='Notif',
            curp='SAHM050101HDFLNAC0',
            curp_archivo=SimpleUploadedFile("curp.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("acta.txt", b"x"),
        )

    def test_aprobado_transition_sends_email(self):
        """Approving a Trabajador sends a notification email."""
        django_mail.outbox = []
        self.trabajador.aprobado = True
        with self.captureOnCommitCallbacks(execute=True):
            self.trabajador.save()
        self.assertEqual(len(django_mail.outbox), 1)
        self.assertIn('notif@test.com', django_mail.outbox[0].to)

    def test_no_email_when_aprobado_unchanged(self):
        """Saving Trabajador without changing aprobado does not send email."""
        self.trabajador.aprobado = False
        django_mail.outbox = []
        with self.captureOnCommitCallbacks(execute=True):
            self.trabajador.save()
        self.assertEqual(len(django_mail.outbox), 0)

    def test_solicitud_estado_change_sends_email(self):
        """Changing solicitud estado triggers a notification email."""
        solicitud = SolicitudAprovechamiento.objects.create(
            becario=self.becario,
            grado=self.grado,
            promedio=9.0,
            boleta=SimpleUploadedFile("b.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r.txt", b"x"),
            ine=SimpleUploadedFile("i.txt", b"x"),
            estado='R',
        )
        django_mail.outbox = []
        solicitud.estado = 'T'
        with self.captureOnCommitCallbacks(execute=True):
            solicitud.save()
        self.assertEqual(len(django_mail.outbox), 1)
        self.assertIn('notif@test.com', django_mail.outbox[0].to)

    def test_solicitud_notas_change_sends_email(self):
        """Changing solicitud notas (without changing estado) triggers a notification email."""
        solicitud = SolicitudAprovechamiento.objects.create(
            becario=self.becario,
            grado=self.grado,
            promedio=9.0,
            boleta=SimpleUploadedFile("b2.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r2.txt", b"x"),
            ine=SimpleUploadedFile("i2.txt", b"x"),
            estado='R',
        )
        django_mail.outbox = []
        solicitud.notas = 'Revisar documento X'
        with self.captureOnCommitCallbacks(execute=True):
            solicitud.save()
        self.assertEqual(len(django_mail.outbox), 1)
        self.assertIn('notif@test.com', django_mail.outbox[0].to)

    def test_solicitud_no_email_when_nothing_changes(self):
        """Saving solicitud without estado/notas changes does not send email."""
        solicitud = SolicitudAprovechamiento.objects.create(
            becario=self.becario,
            grado=self.grado,
            promedio=9.0,
            boleta=SimpleUploadedFile("b3.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r3.txt", b"x"),
            ine=SimpleUploadedFile("i3.txt", b"x"),
            estado='R',
        )
        django_mail.outbox = []
        with self.captureOnCommitCallbacks(execute=True):
            solicitud.save()
        self.assertEqual(len(django_mail.outbox), 0)


# =============================================================================
# Model Unit Tests — __str__ methods
# =============================================================================


class ModelStrMethodTest(TestCase):
    """Tests for the __str__ methods on all models."""

    def test_seccion_str(self):
        s = Seccion.objects.create(numero=42)
        self.assertEqual(str(s), '42')

    def test_puesto_str(self):
        p = Puesto.objects.create(clave='P1234')
        self.assertEqual(str(p), 'P1234')

    def test_jurisdiccion_str(self):
        j = Jurisdiccion.objects.create(clave='JX')
        self.assertEqual(str(j), 'JX')

    def test_lugar_adscripcion_str(self):
        lugar = LugarAdscripcion.objects.create(nombre='Hospital General')
        self.assertEqual(str(lugar), 'Hospital General')

    def test_lugar_adscripcion_alias_null(self):
        lugar = LugarAdscripcion.objects.create(
            nombre='Hospital General', alias=None)
        self.assertIsNone(lugar.alias)
        self.assertEqual(str(lugar), 'Hospital General')

    def test_lugar_adscripcion_alias_set(self):
        lugar = LugarAdscripcion.objects.create(
            nombre='Hospital General', alias='HG')
        self.assertEqual(lugar.alias, 'HG')
        self.assertEqual(str(lugar), 'Hospital General')

    def test_grado_str(self):
        g = Grado.objects.create(clave='G1', nombre='Primero')
        self.assertEqual(str(g), 'G1 - Primero')

    def test_trabajador_str(self):
        user = User.objects.create_user(
            username='SAHM910101HDFLNA01', password='pass')
        seccion = Seccion.objects.create(numero=1)
        puesto = Puesto.objects.create(clave='P1')
        jurisdiccion = Jurisdiccion.objects.create(clave='J1')
        lugar = LugarAdscripcion.objects.create(nombre='L1')
        t = Trabajador.objects.create(
            usuario=user, nombre='A', apellido_paterno='B',
            talon_pago_archivo=SimpleUploadedFile("f.txt", b"x"),
            telefono='1234567890', correo='a@a.com',
            seccion=seccion, puesto=puesto, jurisdiccion=jurisdiccion,
            lugar_adscripcion=lugar,
        )
        self.assertEqual(str(t), 'SAHM910101HDFLNA01')

    def test_becario_str(self):
        user = User.objects.create_user(
            username='SAHM910101HDFLNA02', password='pass')
        b = Becario.objects.create(
            trabajador=user, nombre='X', apellido_paterno='Y',
            curp='SAHM910101HDFLNA03',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        self.assertEqual(str(b), 'SAHM910101HDFLNA03')

    def test_solicitud_aprovechamiento_str(self):
        user = User.objects.create_user(
            username='SAHM910101HDFLNA04', password='pass')
        becario = Becario.objects.create(
            trabajador=user, nombre='X', apellido_paterno='Y',
            curp='SAHM910101HDFLNA05',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        grado = Grado.objects.create(clave='G2', nombre='Segundo')
        s = SolicitudAprovechamiento.objects.create(
            becario=becario, grado=grado, promedio=9.0,
            boleta=SimpleUploadedFile("b.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r.txt", b"x"),
            ine=SimpleUploadedFile("i.txt", b"x"),
            estado='R',
        )
        self.assertIn('SAHM910101HDFLNA05', str(s))
        self.assertIn('R', str(s))

    def test_solicitud_excelencia_str(self):
        user = User.objects.create_user(
            username='SAHM910101HDFLNA06', password='pass')
        becario = Becario.objects.create(
            trabajador=user, nombre='X', apellido_paterno='Y',
            curp='SAHM910101HDFLNA07',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        grado = Grado.objects.create(clave='G3', nombre='Tercero')
        s = SolicitudExcelencia.objects.create(
            becario=becario, grado=grado, promedio=9.5,
            boleta=SimpleUploadedFile("b.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r.txt", b"x"),
            ine=SimpleUploadedFile("i.txt", b"x"),
            carrera='Medicina', estado='P',
        )
        self.assertIn('SAHM910101HDFLNA07', str(s))
        self.assertIn('P', str(s))

    def test_solicitud_especial_str(self):
        user = User.objects.create_user(
            username='SAHM910101HDFLNA08', password='pass')
        becario = Becario.objects.create(
            trabajador=user, nombre='X', apellido_paterno='Y',
            curp='SAHM910101HDFLNA09',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        s = SolicitudEspecial.objects.create(
            becario=becario,
            diagnostico_medico='DX',
            tipo_educacion='Especial',
            certificado_medico=SimpleUploadedFile(
                "cm.txt",
                b"x"),
            certificado_escolar=SimpleUploadedFile(
                "ce.txt",
                b"x"),
            recibo_nomina=SimpleUploadedFile(
                "r.txt",
                b"x"),
            ine=SimpleUploadedFile(
                "i.txt",
                b"x"),
            estado='R',
        )
        self.assertIn('SAHM910101HDFLNA09', str(s))
        self.assertIn('R', str(s))


# =============================================================================
# Model Unit Tests — UniqueConstraint on Solicitud
# =============================================================================


class SolicitudUniqueConstraintTest(TestCase):
    """Tests the database-level unique constraint on pending solicitudes."""

    def setUp(self):
        self.seccion = Seccion.objects.create(numero=1)
        self.puesto = Puesto.objects.create(clave='P1')
        self.jurisdiccion = Jurisdiccion.objects.create(clave='J1')
        self.lugar = LugarAdscripcion.objects.create(nombre='L1')
        self.grado = Grado.objects.create(clave='G1', nombre='Grado 1')
        self.user = User.objects.create_user(
            username='SAHM910101HDFLNA10', password='pass')
        self.becario = Becario.objects.create(
            trabajador=self.user, nombre='X', apellido_paterno='Y',
            curp='SAHM910101HDFLNA11',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )

    def test_unique_constraint_blocks_duplicate_pending(self):
        """Only one solicitud with estado='P' per becario should be allowed."""
        SolicitudAprovechamiento.objects.create(
            becario=self.becario, grado=self.grado, promedio=9.0,
            boleta=SimpleUploadedFile("b1.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r1.txt", b"x"),
            ine=SimpleUploadedFile("i1.txt", b"x"),
            estado='P',
        )
        with self.assertRaises(IntegrityError):
            SolicitudAprovechamiento.objects.create(
                becario=self.becario, grado=self.grado, promedio=8.0,
                boleta=SimpleUploadedFile("b2.txt", b"x"),
                recibo_nomina=SimpleUploadedFile("r2.txt", b"x"),
                ine=SimpleUploadedFile("i2.txt", b"x"),
                estado='P',
            )

    def test_unique_constraint_allows_multiple_non_pending(self):
        """Multiple solicitudes with estado != 'P' are allowed for the same becario."""
        SolicitudAprovechamiento.objects.create(
            becario=self.becario, grado=self.grado, promedio=9.0,
            boleta=SimpleUploadedFile("b1.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r1.txt", b"x"),
            ine=SimpleUploadedFile("i1.txt", b"x"),
            estado='R',
        )
        # Should not raise — duplicate 'R' is allowed
        SolicitudAprovechamiento.objects.create(
            becario=self.becario, grado=self.grado, promedio=8.0,
            boleta=SimpleUploadedFile("b2.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r2.txt", b"x"),
            ine=SimpleUploadedFile("i2.txt", b"x"),
            estado='R',
        )
        self.assertEqual(
            SolicitudAprovechamiento.objects.filter(
                becario=self.becario, estado='R').count(), 2, )

    def test_unique_constraint_allows_different_becarios_pending(self):
        """Two different becarios can each have a pending solicitud."""
        becario2 = Becario.objects.create(
            trabajador=self.user, nombre='Z', apellido_paterno='W',
            curp='SAHM910101HDFLNA12',
            curp_archivo=SimpleUploadedFile("c2.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a2.txt", b"x"),
        )
        SolicitudAprovechamiento.objects.create(
            becario=self.becario, grado=self.grado, promedio=9.0,
            boleta=SimpleUploadedFile("b1.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r1.txt", b"x"),
            ine=SimpleUploadedFile("i1.txt", b"x"),
            estado='P',
        )
        # Different becario — should be fine
        SolicitudAprovechamiento.objects.create(
            becario=becario2, grado=self.grado, promedio=8.0,
            boleta=SimpleUploadedFile("b2.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r2.txt", b"x"),
            ine=SimpleUploadedFile("i2.txt", b"x"),
            estado='P',
        )
        self.assertEqual(
            SolicitudAprovechamiento.objects.filter(estado='P').count(),
            2,
        )

    def test_unique_constraint_cross_type_pending(self):
        """A pending solicitud of one type blocks a pending of another type for the same becario."""
        SolicitudAprovechamiento.objects.create(
            becario=self.becario, grado=self.grado, promedio=9.0,
            boleta=SimpleUploadedFile("b1.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r1.txt", b"x"),
            ine=SimpleUploadedFile("i1.txt", b"x"),
            estado='P',
        )
        # SolicitudExcelencia is a different multi-table-inheritance child,
        # but the constraint is on the base Solicitud table, so it should also
        # be blocked.
        with self.assertRaises(IntegrityError):
            SolicitudExcelencia.objects.create(
                becario=self.becario, grado=self.grado, promedio=9.5,
                boleta=SimpleUploadedFile("b2.txt", b"x"),
                recibo_nomina=SimpleUploadedFile("r2.txt", b"x"),
                ine=SimpleUploadedFile("i2.txt", b"x"),
                carrera='Derecho', estado='P',
            )


# =============================================================================
# Model Unit Tests — Trabajador.save() edge cases
# =============================================================================


class TrabajadorSaveEdgeCaseTest(TestCase):
    """Tests edge cases in Trabajador.save() email notification logic."""

    def setUp(self):
        self.seccion = Seccion.objects.create(numero=1)
        self.puesto = Puesto.objects.create(clave='P1')
        self.jurisdiccion = Jurisdiccion.objects.create(clave='J1')
        self.lugar = LugarAdscripcion.objects.create(nombre='L1')
        self.user = User.objects.create_user(
            username='SAHM910101HDFLNA13', password='pass')

    def test_new_trabajador_does_not_send_approval_email(self):
        """Creating a new Trabajador with aprobado=True should NOT trigger an
        approval email (there's no old record to compare against)."""
        django_mail.outbox = []
        t = Trabajador(
            usuario=self.user, nombre='N', apellido_paterno='T',
            talon_pago_archivo=SimpleUploadedFile("f.txt", b"x"),
            telefono='1234567890', correo='n@t.com',
            seccion=self.seccion, puesto=self.puesto,
            jurisdiccion=self.jurisdiccion, lugar_adscripcion=self.lugar,
            aprobado=True,
        )
        with self.captureOnCommitCallbacks(execute=True):
            t.save()
        self.assertEqual(len(django_mail.outbox), 0)

    def test_aprobado_false_to_false_no_email(self):
        """Saving an already-unapproved Trabajador with no change sends no email."""
        t = Trabajador.objects.create(
            usuario=self.user, nombre='N', apellido_paterno='T',
            talon_pago_archivo=SimpleUploadedFile("f.txt", b"x"),
            telefono='1234567890', correo='n@t.com',
            seccion=self.seccion, puesto=self.puesto,
            jurisdiccion=self.jurisdiccion, lugar_adscripcion=self.lugar,
            aprobado=False,
        )
        django_mail.outbox = []
        t.nombre = 'Updated'
        with self.captureOnCommitCallbacks(execute=True):
            t.save()
        self.assertEqual(len(django_mail.outbox), 0)

    def test_aprobado_true_to_false_no_email(self):
        """Changing aprobado from True to False sends no approval email."""
        t = Trabajador.objects.create(
            usuario=self.user, nombre='N', apellido_paterno='T',
            talon_pago_archivo=SimpleUploadedFile("f.txt", b"x"),
            telefono='1234567890', correo='n@t.com',
            seccion=self.seccion, puesto=self.puesto,
            jurisdiccion=self.jurisdiccion, lugar_adscripcion=self.lugar,
            aprobado=True,
        )
        django_mail.outbox = []
        t.aprobado = False
        with self.captureOnCommitCallbacks(execute=True):
            t.save()
        self.assertEqual(len(django_mail.outbox), 0)

    def test_aprobado_false_to_true_sends_email(self):
        """The canonical happy-path: approving a previously-unapproved worker."""
        t = Trabajador.objects.create(
            usuario=self.user, nombre='N', apellido_paterno='T',
            talon_pago_archivo=SimpleUploadedFile("f.txt", b"x"),
            telefono='1234567890', correo='n@t.com',
            seccion=self.seccion, puesto=self.puesto,
            jurisdiccion=self.jurisdiccion, lugar_adscripcion=self.lugar,
            aprobado=False,
        )
        django_mail.outbox = []
        t.aprobado = True
        with self.captureOnCommitCallbacks(execute=True):
            t.save()
        self.assertEqual(len(django_mail.outbox), 1)


# =============================================================================
# Model Unit Tests — Solicitud.save() edge cases
# =============================================================================


class SolicitudSaveEdgeCaseTest(TestCase):
    """Tests edge cases in Solicitud.save() email notification logic."""

    def setUp(self):
        self.seccion = Seccion.objects.create(numero=1)
        self.puesto = Puesto.objects.create(clave='P1')
        self.jurisdiccion = Jurisdiccion.objects.create(clave='J1')
        self.lugar = LugarAdscripcion.objects.create(nombre='L1')
        self.grado = Grado.objects.create(clave='G1', nombre='Grado 1')
        self.user = User.objects.create_user(
            username='SAHM910101HDFLNA14', password='pass')
        self.trabajador = Trabajador.objects.create(
            usuario=self.user, nombre='A', apellido_paterno='B',
            talon_pago_archivo=SimpleUploadedFile("f.txt", b"x"),
            telefono='1234567890', correo='a@b.com',
            seccion=self.seccion, puesto=self.puesto,
            jurisdiccion=self.jurisdiccion, lugar_adscripcion=self.lugar,
            aprobado=True,
        )
        self.becario = Becario.objects.create(
            trabajador=self.user, nombre='X', apellido_paterno='Y',
            curp='SAHM910101HDFLNA15',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )

    def test_new_solicitud_does_not_send_email(self):
        """Creating a new solicitud (no old record) should NOT trigger a status email."""
        django_mail.outbox = []
        s = SolicitudAprovechamiento(
            becario=self.becario, grado=self.grado, promedio=9.0,
            boleta=SimpleUploadedFile("b.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r.txt", b"x"),
            ine=SimpleUploadedFile("i.txt", b"x"),
            estado='R',
        )
        with self.captureOnCommitCallbacks(execute=True):
            s.save()
        self.assertEqual(len(django_mail.outbox), 0)

    def test_both_estado_and_notas_change_sends_one_email(self):
        """When both estado and notas change, only one email should be sent."""
        s = SolicitudAprovechamiento.objects.create(
            becario=self.becario, grado=self.grado, promedio=9.0,
            boleta=SimpleUploadedFile("b.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r.txt", b"x"),
            ine=SimpleUploadedFile("i.txt", b"x"),
            estado='R',
        )
        django_mail.outbox = []
        s.estado = 'T'
        s.notas = 'Updated notes'
        with self.captureOnCommitCallbacks(execute=True):
            s.save()
        self.assertEqual(len(django_mail.outbox), 1)

    @patch('becas_sntsa.models.EmailMessage.send',
           side_effect=smtplib.SMTPException('fail'))
    def test_solicitud_save_does_not_fail_on_email_error(self, mock_send):
        """Solicitud.save() should succeed even when email sending fails."""
        s = SolicitudAprovechamiento.objects.create(
            becario=self.becario, grado=self.grado, promedio=9.0,
            boleta=SimpleUploadedFile("b.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r.txt", b"x"),
            ine=SimpleUploadedFile("i.txt", b"x"),
            estado='R',
        )
        s.estado = 'T'
        with self.captureOnCommitCallbacks(execute=True):
            s.save()
        s.refresh_from_db()
        self.assertEqual(s.estado, 'T')
        self.assertEqual(mock_send.call_count, 1)


# =============================================================================
# Unit Tests — validar_curp function
# =============================================================================


class ValidarCurpTest(TestCase):
    """Tests for the validar_curp validation function."""

    def test_valid_curp_male(self):
        try:
            validar_curp('SAHM910101HDFLNA01')
        except ValidationError:
            self.fail('validar_curp raised ValidationError for a valid CURP')

    def test_valid_curp_female(self):
        try:
            validar_curp('SAHM910101MDFLNA02')
        except ValidationError:
            self.fail('validar_curp raised ValidationError for a valid CURP')

    def test_invalid_curp_too_short(self):
        with self.assertRaises(ValidationError):
            validar_curp('SAHM910101HDFLNA')

    def test_invalid_curp_lowercase(self):
        # validar_curp expects uppercase
        with self.assertRaises(ValidationError):
            validar_curp('sahm910101hdflna01')

    def test_invalid_curp_bad_format(self):
        with self.assertRaises(ValidationError):
            validar_curp('NOT-A-VALID-CURP!!')

    def test_invalid_curp_empty(self):
        with self.assertRaises(ValidationError):
            validar_curp('')


# =============================================================================
# Unit Tests — Form validation
# =============================================================================


class FormValidationTest(TestCase):
    """Unit tests for form validation logic."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='SAHM910101HDFLNA16', password='pass')
        self.grado = Grado.objects.create(clave='G1', nombre='Grado 1')

    # --- BecarioCreateForm ---

    def test_becario_create_form_valid(self):
        form = BecarioCreateForm(
            data={
                'nombre': 'Test', 'apellido_paterno': 'Becario',
                'curp': 'SAHM910101HDFLNA17',
            },
            files={
                'curp_archivo': SimpleUploadedFile("c.txt", b"x"),
                'acta_nacimiento': SimpleUploadedFile("a.txt", b"x"),
            },
        )
        self.assertTrue(form.is_valid())

    def test_becario_create_form_invalid_curp(self):
        form = BecarioCreateForm({
            'nombre': 'Test', 'apellido_paterno': 'Becario',
            'curp': 'INVALID',
            'curp_archivo': SimpleUploadedFile("c.txt", b"x"),
            'acta_nacimiento': SimpleUploadedFile("a.txt", b"x"),
        })
        self.assertFalse(form.is_valid())
        self.assertIn('curp', form.errors)

    def test_becario_create_form_uppercases_curp(self):
        """clean_curp should uppercase the CURP value."""
        form = BecarioCreateForm(
            data={
                'nombre': 'Test', 'apellido_paterno': 'Becario',
                'curp': 'sahm910101hdflna18',
            },
            files={
                'curp_archivo': SimpleUploadedFile("c.txt", b"x"),
                'acta_nacimiento': SimpleUploadedFile("a.txt", b"x"),
            },
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['curp'], 'SAHM910101HDFLNA18')

    def test_becario_create_form_missing_required(self):
        form = BecarioCreateForm({})
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)
        self.assertIn('curp', form.errors)

    # --- BecarioEditForm ---

    def test_becario_edit_form_valid(self):
        form = BecarioEditForm(
            data={
                'nombre': 'Test', 'apellido_paterno': 'Becario',
                'curp': 'SAHM910101HDFLNA19',
            },
            files={
                'curp_archivo': SimpleUploadedFile("c.txt", b"x"),
                'acta_nacimiento': SimpleUploadedFile("a.txt", b"x"),
            },
        )
        self.assertTrue(form.is_valid())

    def test_becario_edit_form_invalid_curp(self):
        form = BecarioEditForm(
            {'nombre': 'X', 'apellido_paterno': 'Y', 'curp': 'bad'})
        self.assertFalse(form.is_valid())
        self.assertIn('curp', form.errors)

    # --- SolicitudAprovechamientoCreateForm ---

    def test_aprov_form_promedio_valid_min(self):
        becario = Becario.objects.create(
            trabajador=self.user, nombre='X', apellido_paterno='Y',
            curp='SAHM910101HDFLNA20',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        form = SolicitudAprovechamientoCreateForm(
            data={
                'becario': becario.id, 'grado': self.grado.id, 'promedio': 6.0}, files={
                'boleta': SimpleUploadedFile(
                    "b.txt", b"x"), 'recibo_nomina': SimpleUploadedFile(
                    "r.txt", b"x"), 'ine': SimpleUploadedFile(
                        "i.txt", b"x"), }, user=self.user, )
        if not form.is_valid():
            self.fail(f'Form unexpectedly invalid, errors={form.errors}')

    def test_aprov_form_promedio_valid_max(self):
        becario = Becario.objects.create(
            trabajador=self.user, nombre='X', apellido_paterno='Y',
            curp='SAHM910101HDFLNA21',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        form = SolicitudAprovechamientoCreateForm(
            data={
                'becario': becario.id, 'grado': self.grado.id, 'promedio': 10.0}, files={
                'boleta': SimpleUploadedFile(
                    "b.txt", b"x"), 'recibo_nomina': SimpleUploadedFile(
                    "r.txt", b"x"), 'ine': SimpleUploadedFile(
                        "i.txt", b"x"), }, user=self.user, )
        if not form.is_valid():
            self.fail(f'Form unexpectedly invalid, errors={form.errors}')

    def test_aprov_form_promedio_below_min(self):
        becario = Becario.objects.create(
            trabajador=self.user, nombre='X', apellido_paterno='Y',
            curp='SAHM910101HDFLNA22',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        form = SolicitudAprovechamientoCreateForm(
            data={
                'becario': becario.id, 'grado': self.grado.id, 'promedio': 5.9}, files={
                'boleta': SimpleUploadedFile(
                    "b.txt", b"x"), 'recibo_nomina': SimpleUploadedFile(
                    "r.txt", b"x"), 'ine': SimpleUploadedFile(
                        "i.txt", b"x"), }, user=self.user, )
        self.assertFalse(form.is_valid())
        self.assertIn('promedio', form.errors)

    def test_aprov_form_promedio_above_max(self):
        becario = Becario.objects.create(
            trabajador=self.user, nombre='X', apellido_paterno='Y',
            curp='SAHM910101HDFLNA23',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        form = SolicitudAprovechamientoCreateForm(
            data={
                'becario': becario.id, 'grado': self.grado.id, 'promedio': 10.1}, files={
                'boleta': SimpleUploadedFile(
                    "b.txt", b"x"), 'recibo_nomina': SimpleUploadedFile(
                    "r.txt", b"x"), 'ine': SimpleUploadedFile(
                        "i.txt", b"x"), }, user=self.user, )
        self.assertFalse(form.is_valid())
        self.assertIn('promedio', form.errors)

    def test_aprov_form_becario_queryset_filtered(self):
        """The becario queryset should only include the current user's becarios."""
        other_user = User.objects.create_user(
            username='OTR910101HDFLNA01', password='pass')
        other_becario = Becario.objects.create(
            trabajador=other_user, nombre='O', apellido_paterno='T',
            curp='OTR910101HDFLNA02',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        my_becario = Becario.objects.create(
            trabajador=self.user, nombre='M', apellido_paterno='Y',
            curp='SAHM910101HDFLNA24',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        form = SolicitudAprovechamientoCreateForm(user=self.user)
        queryset = form.fields['becario'].queryset
        self.assertIn(my_becario, queryset)
        self.assertNotIn(other_becario, queryset)

    # --- SolicitudExcelenciaCreateForm ---

    def test_excelencia_form_promedio_below_min(self):
        becario = Becario.objects.create(
            trabajador=self.user, nombre='X', apellido_paterno='Y',
            curp='SAHM910101HDFLNA25',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        form = SolicitudExcelenciaCreateForm(
            data={
                'becario': becario.id,
                'grado': self.grado.id,
                'promedio': 5.0,
                'carrera': 'Med'},
            files={
                'boleta': SimpleUploadedFile(
                    "b.txt",
                    b"x"),
                'recibo_nomina': SimpleUploadedFile(
                    "r.txt",
                    b"x"),
                'ine': SimpleUploadedFile(
                    "i.txt",
                    b"x"),
            },
            user=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('promedio', form.errors)

    def test_excelencia_form_promedio_above_max(self):
        becario = Becario.objects.create(
            trabajador=self.user, nombre='X', apellido_paterno='Y',
            curp='SAHM910101HDFLNA26',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        form = SolicitudExcelenciaCreateForm(
            data={
                'becario': becario.id,
                'grado': self.grado.id,
                'promedio': 11.0,
                'carrera': 'Med'},
            files={
                'boleta': SimpleUploadedFile(
                    "b.txt",
                    b"x"),
                'recibo_nomina': SimpleUploadedFile(
                    "r.txt",
                    b"x"),
                'ine': SimpleUploadedFile(
                    "i.txt",
                    b"x"),
            },
            user=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('promedio', form.errors)

    def test_excelencia_form_valid(self):
        becario = Becario.objects.create(
            trabajador=self.user, nombre='X', apellido_paterno='Y',
            curp='SAHM910101HDFLNA27',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        form = SolicitudExcelenciaCreateForm(
            data={
                'becario': becario.id,
                'grado': self.grado.id,
                'promedio': 9.0,
                'carrera': 'Medicina'},
            files={
                'boleta': SimpleUploadedFile(
                    "b.txt",
                    b"x"),
                'recibo_nomina': SimpleUploadedFile(
                    "r.txt",
                    b"x"),
                'ine': SimpleUploadedFile(
                    "i.txt",
                    b"x"),
            },
            user=self.user,
        )
        if not form.is_valid():
            self.fail(f'Form unexpectedly invalid, errors={form.errors}')

    def test_excelencia_form_becario_queryset_filtered(self):
        other_user = User.objects.create_user(
            username='OTR910101HDFLNA03', password='pass')
        other_becario = Becario.objects.create(
            trabajador=other_user, nombre='O', apellido_paterno='T',
            curp='OTR910101HDFLNA04',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        my_becario = Becario.objects.create(
            trabajador=self.user, nombre='M', apellido_paterno='Y',
            curp='SAHM910101HDFLNA28',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        form = SolicitudExcelenciaCreateForm(user=self.user)
        queryset = form.fields['becario'].queryset
        self.assertIn(my_becario, queryset)
        self.assertNotIn(other_becario, queryset)

    # --- SolicitudEspecialCreateForm ---

    def test_especial_form_valid(self):
        becario = Becario.objects.create(
            trabajador=self.user, nombre='X', apellido_paterno='Y',
            curp='SAHM910101HDFLNA29',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        form = SolicitudEspecialCreateForm(
            data={
                'becario': becario.id,
                'diagnostico_medico': 'DX Test',
                'tipo_educacion': 'Especial',
            },
            files={
                'certificado_medico': SimpleUploadedFile("cm.txt", b"x"),
                'certificado_escolar': SimpleUploadedFile("ce.txt", b"x"),
                'recibo_nomina': SimpleUploadedFile("r.txt", b"x"),
                'ine': SimpleUploadedFile("i.txt", b"x"),
            },
            user=self.user,
        )
        if not form.is_valid():
            self.fail(f'Form unexpectedly invalid, errors={form.errors}')

    def test_especial_form_becario_queryset_filtered(self):
        other_user = User.objects.create_user(
            username='OTR910101HDFLNA05', password='pass')
        other_becario = Becario.objects.create(
            trabajador=other_user, nombre='O', apellido_paterno='T',
            curp='OTR910101HDFLNA06',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        my_becario = Becario.objects.create(
            trabajador=self.user, nombre='M', apellido_paterno='Y',
            curp='SAHM910101HDFLNA30',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        form = SolicitudEspecialCreateForm(user=self.user)
        queryset = form.fields['becario'].queryset
        self.assertIn(my_becario, queryset)
        self.assertNotIn(other_becario, queryset)

    def test_especial_form_missing_required(self):
        form = SolicitudEspecialCreateForm(data={}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('becario', form.errors)
        self.assertIn('diagnostico_medico', form.errors)


# =============================================================================
# Unit Test — Template tag add_class
# =============================================================================


class TemplateTagTest(TestCase):
    """Tests for custom template tags."""

    def test_add_class_filter(self):
        from becas_sntsa.templatetags.form_tags import add_class
        from django import forms

        class DummyForm(forms.Form):
            name = forms.CharField()

        f = DummyForm()
        result = add_class(f['name'], 'my-class')
        self.assertIn('class="my-class"', result)


# =============================================================================
# Integration Tests — Views not yet covered
# =============================================================================


class HomeViewTest(TestCase):
    """Tests for the home page."""

    def test_home_view_returns_200(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')


class VerBecariosViewTest(TestCase):
    """Tests for the ver_becarios view."""

    def setUp(self):
        self.seccion = Seccion.objects.create(numero=1)
        self.puesto = Puesto.objects.create(clave='P1')
        self.jurisdiccion = Jurisdiccion.objects.create(clave='J1')
        self.lugar = LugarAdscripcion.objects.create(nombre='L1')
        self.user = User.objects.create_user(
            username='SAHM910101HDFLNA31', password='pass')
        self.trabajador = Trabajador.objects.create(
            usuario=self.user, nombre='A', apellido_paterno='B',
            talon_pago_archivo=SimpleUploadedFile("f.txt", b"x"),
            telefono='1234567890', correo='a@b.com',
            seccion=self.seccion, puesto=self.puesto,
            jurisdiccion=self.jurisdiccion, lugar_adscripcion=self.lugar,
            aprobado=True,
        )
        self.client.login(username='SAHM910101HDFLNA31', password='pass')

    def test_ver_becarios_lists_users_becarios(self):
        _ = Becario.objects.create(
            trabajador=self.user, nombre='B1', apellido_paterno='X',
            curp='SAHM910101HDFLNA32',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        _ = Becario.objects.create(
            trabajador=self.user, nombre='B2', apellido_paterno='Y',
            curp='SAHM910101HDFLNA33',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        response = self.client.get(reverse('ver_becarios'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ver_becarios.html')
        self.assertContains(response, 'B1')
        self.assertContains(response, 'B2')

    def test_ver_becarios_only_shows_own_becarios(self):
        other_user = User.objects.create_user(
            username='OTR910101HDFLNA07', password='pass')
        _ = Becario.objects.create(
            trabajador=other_user, nombre='Other', apellido_paterno='B',
            curp='OTR910101HDFLNA08',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        response = self.client.get(reverse('ver_becarios'))
        self.assertNotContains(response, 'Other')

    def test_ver_becarios_empty(self):
        response = self.client.get(reverse('ver_becarios'))
        self.assertEqual(response.status_code, 200)


class VerSolicitudesViewTest(TestCase):
    """Tests for the ver_solicitudes view."""

    def setUp(self):
        self.seccion = Seccion.objects.create(numero=1)
        self.puesto = Puesto.objects.create(clave='P1')
        self.jurisdiccion = Jurisdiccion.objects.create(clave='J1')
        self.lugar = LugarAdscripcion.objects.create(nombre='L1')
        self.grado = Grado.objects.create(clave='G1', nombre='Grado 1')
        self.user = User.objects.create_user(
            username='SAHM910101HDFLNA34', password='pass')
        self.trabajador = Trabajador.objects.create(
            usuario=self.user, nombre='A', apellido_paterno='B',
            talon_pago_archivo=SimpleUploadedFile("f.txt", b"x"),
            telefono='1234567890', correo='a@b.com',
            seccion=self.seccion, puesto=self.puesto,
            jurisdiccion=self.jurisdiccion, lugar_adscripcion=self.lugar,
            aprobado=True,
        )
        self.becario = Becario.objects.create(
            trabajador=self.user, nombre='B', apellido_paterno='X',
            curp='SAHM910101HDFLNA35',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        self.client.login(username='SAHM910101HDFLNA34', password='pass')

    def test_ver_solicitudes_shows_all_types(self):
        _ = SolicitudAprovechamiento.objects.create(
            becario=self.becario, grado=self.grado, promedio=9.0,
            boleta=SimpleUploadedFile("b.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r.txt", b"x"),
            ine=SimpleUploadedFile("i.txt", b"x"),
            estado='R',
        )
        _ = SolicitudExcelencia.objects.create(
            becario=self.becario, grado=self.grado, promedio=9.5,
            boleta=SimpleUploadedFile("b.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r.txt", b"x"),
            ine=SimpleUploadedFile("i.txt", b"x"),
            carrera='Medicina', estado='P',
        )
        _ = SolicitudEspecial.objects.create(
            becario=self.becario, diagnostico_medico='DX', tipo_educacion='E',
            certificado_medico=SimpleUploadedFile("cm.txt", b"x"),
            certificado_escolar=SimpleUploadedFile("ce.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r.txt", b"x"),
            ine=SimpleUploadedFile("i.txt", b"x"),
            estado='T',
        )
        response = self.client.get(reverse('ver_solicitudes'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ver_solicitudes.html')

    def test_ver_solicitudes_empty(self):
        response = self.client.get(reverse('ver_solicitudes'))
        self.assertEqual(response.status_code, 200)


class CreateSolicitudExcelenciaViewTest(TestCase):
    """Integration tests for the create_solicitud_excelencia view."""

    def setUp(self):
        self.seccion = Seccion.objects.create(numero=1)
        self.puesto = Puesto.objects.create(clave='P1')
        self.jurisdiccion = Jurisdiccion.objects.create(clave='J1')
        self.lugar = LugarAdscripcion.objects.create(nombre='L1')
        self.grado = Grado.objects.create(clave='G1', nombre='Grado 1')
        self.user = User.objects.create_user(
            username='SAHM910101HDFLNA36', password='pass')
        self.trabajador = Trabajador.objects.create(
            usuario=self.user, nombre='A', apellido_paterno='B',
            talon_pago_archivo=SimpleUploadedFile("f.txt", b"x"),
            telefono='1234567890', correo='a@b.com',
            seccion=self.seccion, puesto=self.puesto,
            jurisdiccion=self.jurisdiccion, lugar_adscripcion=self.lugar,
            aprobado=True,
        )
        self.becario = Becario.objects.create(
            trabajador=self.user, nombre='B', apellido_paterno='X',
            curp='SAHM910101HDFLNA37',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        self.client.login(username='SAHM910101HDFLNA36', password='pass')

    def test_create_excelencia_get(self):
        response = self.client.get(reverse('create_solicitud_excelencia'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_solicitud_excelencia.html')

    def test_create_excelencia_post_success(self):
        data = {
            'becario': self.becario.id,
            'grado': self.grado.id,
            'promedio': 9.5,
            'carrera': 'Medicina',
            'boleta': SimpleUploadedFile("b.txt", b"x"),
            'recibo_nomina': SimpleUploadedFile("r.txt", b"x"),
            'ine': SimpleUploadedFile("i.txt", b"x"),
        }
        response = self.client.post(
            reverse('create_solicitud_excelencia'), data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            SolicitudExcelencia.objects.filter(
                becario=self.becario,
                carrera='Medicina').exists())

    def test_create_excelencia_duplicate_rejected(self):
        SolicitudExcelencia.objects.create(
            becario=self.becario, grado=self.grado, promedio=9.0,
            boleta=SimpleUploadedFile("b.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r.txt", b"x"),
            ine=SimpleUploadedFile("i.txt", b"x"),
            carrera='Derecho', estado='R',
        )
        data = {
            'becario': self.becario.id,
            'grado': self.grado.id,
            'promedio': 9.5,
            'carrera': 'Medicina',
            'boleta': SimpleUploadedFile("b2.txt", b"x"),
            'recibo_nomina': SimpleUploadedFile("r2.txt", b"x"),
            'ine': SimpleUploadedFile("i2.txt", b"x"),
        }
        response = self.client.post(
            reverse('create_solicitud_excelencia'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, 'El becario ya tiene una solicitud pendiente')


class CreateSolicitudEspecialViewTest(TestCase):
    """Integration tests for the create_solicitud_especial view."""

    def setUp(self):
        self.seccion = Seccion.objects.create(numero=1)
        self.puesto = Puesto.objects.create(clave='P1')
        self.jurisdiccion = Jurisdiccion.objects.create(clave='J1')
        self.lugar = LugarAdscripcion.objects.create(nombre='L1')
        self.user = User.objects.create_user(
            username='SAHM910101HDFLNA38', password='pass')
        self.trabajador = Trabajador.objects.create(
            usuario=self.user, nombre='A', apellido_paterno='B',
            talon_pago_archivo=SimpleUploadedFile("f.txt", b"x"),
            telefono='1234567890', correo='a@b.com',
            seccion=self.seccion, puesto=self.puesto,
            jurisdiccion=self.jurisdiccion, lugar_adscripcion=self.lugar,
            aprobado=True,
        )
        self.becario = Becario.objects.create(
            trabajador=self.user, nombre='B', apellido_paterno='X',
            curp='SAHM910101HDFLNA39',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        self.client.login(username='SAHM910101HDFLNA38', password='pass')

    def test_create_especial_get(self):
        response = self.client.get(reverse('create_solicitud_especial'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_solicitud_especial.html')

    def test_create_especial_post_success(self):
        data = {
            'becario': self.becario.id,
            'diagnostico_medico': 'DX Test',
            'tipo_educacion': 'Especial',
            'certificado_medico': SimpleUploadedFile("cm.txt", b"x"),
            'certificado_escolar': SimpleUploadedFile("ce.txt", b"x"),
            'recibo_nomina': SimpleUploadedFile("r.txt", b"x"),
            'ine': SimpleUploadedFile("i.txt", b"x"),
        }
        response = self.client.post(
            reverse('create_solicitud_especial'), data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            SolicitudEspecial.objects.filter(
                becario=self.becario,
                diagnostico_medico='DX Test').exists())

    def test_create_especial_duplicate_rejected(self):
        SolicitudEspecial.objects.create(
            becario=self.becario, diagnostico_medico='DX', tipo_educacion='E',
            certificado_medico=SimpleUploadedFile("cm.txt", b"x"),
            certificado_escolar=SimpleUploadedFile("ce.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r.txt", b"x"),
            ine=SimpleUploadedFile("i.txt", b"x"),
            estado='R',
        )
        data = {
            'becario': self.becario.id,
            'diagnostico_medico': 'DX2',
            'tipo_educacion': 'E2',
            'certificado_medico': SimpleUploadedFile("cm2.txt", b"x"),
            'certificado_escolar': SimpleUploadedFile("ce2.txt", b"x"),
            'recibo_nomina': SimpleUploadedFile("r2.txt", b"x"),
            'ine': SimpleUploadedFile("i2.txt", b"x"),
        }
        response = self.client.post(reverse('create_solicitud_especial'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, 'El becario ya tiene una solicitud pendiente')


class EditarUsuarioViewTest(TestCase):
    """Integration tests for the editar_usuario view."""

    def setUp(self):
        self.seccion = Seccion.objects.create(numero=1)
        self.puesto = Puesto.objects.create(clave='P1')
        self.jurisdiccion = Jurisdiccion.objects.create(clave='J1')
        self.lugar = LugarAdscripcion.objects.create(nombre='L1')
        self.user = User.objects.create_user(
            username='SAHM910101HDFLNA40',
            password='pass',
            email='old@test.com',
        )
        self.trabajador = Trabajador.objects.create(
            usuario=self.user, nombre='A', apellido_paterno='B',
            talon_pago_archivo=SimpleUploadedFile("f.txt", b"x"),
            telefono='1234567890', correo='old@test.com',
            seccion=self.seccion, puesto=self.puesto,
            jurisdiccion=self.jurisdiccion, lugar_adscripcion=self.lugar,
            aprobado=True,
        )
        self.client.login(username='SAHM910101HDFLNA40', password='pass')

    def test_editar_usuario_get(self):
        response = self.client.get(reverse('editar_usuario'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'editar_usuario.html')

    def test_editar_usuario_post_update_phone(self):
        """Updating the phone number should succeed without triggering email change."""
        response = self.client.post(reverse('editar_usuario'), {
            'telefono': '9999999999',
            'correo': 'old@test.com',
            'talon_pago_archivo': SimpleUploadedFile("f2.txt", b"x"),
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.trabajador.refresh_from_db()
        self.assertEqual(self.trabajador.telefono, '9999999999')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_editar_usuario_email_change_sets_pending(self):
        """Changing email should store it in pending_email and send verification."""
        django_mail.outbox = []
        response = self.client.post(reverse('editar_usuario'), {
            'telefono': '1234567890',
            'correo': 'new@test.com',
            'talon_pago_archivo': SimpleUploadedFile("f2.txt", b"x"),
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'espera_verificacion_nuevo_email.html')

        self.trabajador.refresh_from_db()
        self.assertEqual(self.trabajador.correo, 'old@test.com')  # unchanged
        self.assertEqual(self.trabajador.pending_email, 'new@test.com')
        self.assertEqual(len(django_mail.outbox), 1)

    def test_editar_usuario_invalid_form(self):
        """Submitting an invalid form re-renders with errors."""
        response = self.client.post(reverse('editar_usuario'), {
            'telefono': '',  # required field blank
            'correo': 'not-an-email',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'editar_usuario.html')


class EditarBecarioViewTest(TestCase):
    """Integration tests for the editar_becario view."""

    def setUp(self):
        self.seccion = Seccion.objects.create(numero=1)
        self.puesto = Puesto.objects.create(clave='P1')
        self.jurisdiccion = Jurisdiccion.objects.create(clave='J1')
        self.lugar = LugarAdscripcion.objects.create(nombre='L1')
        self.user = User.objects.create_user(
            username='SAHM910101HDFLNA41', password='pass')
        self.trabajador = Trabajador.objects.create(
            usuario=self.user, nombre='A', apellido_paterno='B',
            talon_pago_archivo=SimpleUploadedFile("f.txt", b"x"),
            telefono='1234567890', correo='a@b.com',
            seccion=self.seccion, puesto=self.puesto,
            jurisdiccion=self.jurisdiccion, lugar_adscripcion=self.lugar,
            aprobado=True,
        )
        self.becario = Becario.objects.create(
            trabajador=self.user, nombre='B', apellido_paterno='X',
            curp='SAHM910101HDFLNA42',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        self.client.login(username='SAHM910101HDFLNA41', password='pass')

    def test_editar_becario_get(self):
        response = self.client.get(
            reverse(
                'editar_becario', args=[
                    self.becario.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'editar_becario.html')

    def test_editar_becario_post_success(self):
        response = self.client.post(
            reverse('editar_becario', args=[self.becario.id]),
            {
                'nombre': 'Updated',
                'apellido_paterno': 'Name',
                'curp': 'SAHM910101HDFLNA43',
                'curp_archivo': SimpleUploadedFile("c2.txt", b"x"),
                'acta_nacimiento': SimpleUploadedFile("a2.txt", b"x"),
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ver_becarios.html')
        self.becario.refresh_from_db()
        self.assertEqual(self.becario.nombre, 'Updated')

    def test_editar_becario_blocked_with_active_solicitud(self):
        """Should be blocked when the becario has a solicitud with estado in ['R', 'P', 'T']."""
        grado = Grado.objects.create(clave='G1', nombre='Grado 1')
        SolicitudAprovechamiento.objects.create(
            becario=self.becario, grado=grado, promedio=9.0,
            boleta=SimpleUploadedFile("b.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r.txt", b"x"),
            ine=SimpleUploadedFile("i.txt", b"x"),
            estado='R',
        )
        response = self.client.get(
            reverse(
                'editar_becario', args=[
                    self.becario.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, 'Este becario tiene una solicitud en curso')

    def test_editar_becario_allowed_with_finalizado_solicitud(self):
        """Should be allowed when the becario only has solicitud with estado='F'."""
        grado = Grado.objects.create(clave='G1', nombre='Grado 1')
        SolicitudAprovechamiento.objects.create(
            becario=self.becario, grado=grado, promedio=9.0,
            boleta=SimpleUploadedFile("b.txt", b"x"),
            recibo_nomina=SimpleUploadedFile("r.txt", b"x"),
            ine=SimpleUploadedFile("i.txt", b"x"),
            estado='F',
        )
        response = self.client.get(
            reverse(
                'editar_becario', args=[
                    self.becario.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'editar_becario.html')

    def test_editar_becario_404_for_other_users_becario(self):
        other_user = User.objects.create_user(
            username='OTR910101HDFLNA09', password='pass')
        other_becario = Becario.objects.create(
            trabajador=other_user, nombre='O', apellido_paterno='T',
            curp='OTR910101HDFLNA10',
            curp_archivo=SimpleUploadedFile("c.txt", b"x"),
            acta_nacimiento=SimpleUploadedFile("a.txt", b"x"),
        )
        response = self.client.get(
            reverse(
                'editar_becario', args=[
                    other_becario.id]))
        self.assertEqual(response.status_code, 404)


class CreateSolicitudAprovGetViewTest(TestCase):
    """Test the GET of create_solicitud_aprovechamiento (not covered elsewhere)."""

    def setUp(self):
        self.seccion = Seccion.objects.create(numero=1)
        self.puesto = Puesto.objects.create(clave='P1')
        self.jurisdiccion = Jurisdiccion.objects.create(clave='J1')
        self.lugar = LugarAdscripcion.objects.create(nombre='L1')
        self.user = User.objects.create_user(
            username='SAHM910101HDFLNA44', password='pass')
        self.trabajador = Trabajador.objects.create(
            usuario=self.user, nombre='A', apellido_paterno='B',
            talon_pago_archivo=SimpleUploadedFile("f.txt", b"x"),
            telefono='1234567890', correo='a@b.com',
            seccion=self.seccion, puesto=self.puesto,
            jurisdiccion=self.jurisdiccion, lugar_adscripcion=self.lugar,
            aprobado=True,
        )
        self.client.login(username='SAHM910101HDFLNA44', password='pass')

    def test_create_solicitud_aprov_get(self):
        response = self.client.get(reverse('create_solicitud_aprovechamiento'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'create_solicitud_aprovechamiento.html')


class SignupEdgeCaseTest(TestCase):
    """Edge case tests for the signup view."""

    def test_signup_duplicate_username(self):
        User.objects.create_user(
            username='SAHM910101HDFLNA45',
            password='pass')
        response = self.client.post(reverse('signup'), {
            'username': 'SAHM910101HDFLNA45',
            'password1': 'newpassword',
            'password2': 'newpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'El usuario ya existe')


class DownloadFileBecarioAndSolicitudTest(TestCase):
    """Tests for download_file covering becario and solicitud files for non-staff users."""

    def setUp(self):
        self.seccion = Seccion.objects.create(numero=1)
        self.puesto = Puesto.objects.create(clave='P1')
        self.jurisdiccion = Jurisdiccion.objects.create(clave='J1')
        self.lugar = LugarAdscripcion.objects.create(nombre='L1')
        self.grado = Grado.objects.create(clave='G1', nombre='Grado 1')

        self.owner_user = User.objects.create_user(
            username='SAHM910101HDFLNA46', password='pass')
        self.trabajador = Trabajador.objects.create(
            usuario=self.owner_user, nombre='A', apellido_paterno='B',
            talon_pago_archivo=SimpleUploadedFile("talon.txt", b"talon"),
            telefono='1234567890', correo='a@b.com',
            seccion=self.seccion, puesto=self.puesto,
            jurisdiccion=self.jurisdiccion, lugar_adscripcion=self.lugar,
            aprobado=True,
        )
        self.becario = Becario.objects.create(
            trabajador=self.owner_user, nombre='B', apellido_paterno='X',
            curp='SAHM910101HDFLNA47',
            curp_archivo=SimpleUploadedFile("curp.txt", b"curp"),
            acta_nacimiento=SimpleUploadedFile("acta.txt", b"acta"),
        )
        self.solicitud_aprov = SolicitudAprovechamiento.objects.create(
            becario=self.becario, grado=self.grado, promedio=9.0,
            boleta=SimpleUploadedFile("boleta.txt", b"boleta"),
            recibo_nomina=SimpleUploadedFile("rn.txt", b"rn"),
            ine=SimpleUploadedFile("ine.txt", b"ine"),
            estado='R',
        )
        self.other_user = User.objects.create_user(
            username='SAHM910101HDFLNA48', password='pass')

    def test_owner_can_download_own_becario_curp_file(self):
        self.client.login(username='SAHM910101HDFLNA46', password='pass')
        response = self.client.get(
            reverse(
                'download_file', args=[
                    self.becario.curp_archivo.name]))
        self.assertEqual(response.status_code, 200)

    def test_owner_can_download_own_becario_acta_file(self):
        self.client.login(username='SAHM910101HDFLNA46', password='pass')
        response = self.client.get(
            reverse(
                'download_file', args=[
                    self.becario.acta_nacimiento.name]))
        self.assertEqual(response.status_code, 200)

    def test_owner_can_download_own_solicitud_recibo(self):
        self.client.login(username='SAHM910101HDFLNA46', password='pass')
        response = self.client.get(
            reverse(
                'download_file', args=[
                    self.solicitud_aprov.recibo_nomina.name]))
        self.assertEqual(response.status_code, 200)

    def test_owner_can_download_own_solicitud_ine(self):
        self.client.login(username='SAHM910101HDFLNA46', password='pass')
        response = self.client.get(
            reverse(
                'download_file', args=[
                    self.solicitud_aprov.ine.name]))
        self.assertEqual(response.status_code, 200)

    def test_owner_can_download_own_solicitud_boleta(self):
        self.client.login(username='SAHM910101HDFLNA46', password='pass')
        response = self.client.get(
            reverse(
                'download_file', args=[
                    self.solicitud_aprov.boleta.name]))
        self.assertEqual(response.status_code, 200)

    def test_other_user_cannot_download_becario_curp(self):
        self.client.login(username='SAHM910101HDFLNA48', password='pass')
        response = self.client.get(
            reverse(
                'download_file', args=[
                    self.becario.curp_archivo.name]))
        self.assertEqual(response.status_code, 403)

    def test_other_user_cannot_download_solicitud_file(self):
        self.client.login(username='SAHM910101HDFLNA48', password='pass')
        response = self.client.get(
            reverse(
                'download_file', args=[
                    self.solicitud_aprov.boleta.name]))
        self.assertEqual(response.status_code, 403)

    def tearDown(self):
        for obj in [
            self.trabajador.talon_pago_archivo,
            self.becario.curp_archivo,
            self.becario.acta_nacimiento,
            self.solicitud_aprov.boleta,
            self.solicitud_aprov.recibo_nomina,
            self.solicitud_aprov.ine,
        ]:
            if obj:
                file_path = os.path.join(settings.MEDIA_ROOT, obj.name)
                if os.path.exists(file_path):
                    os.remove(file_path)


class CreateTrabajadorEdgeCaseTest(TestCase):
    """Edge case tests for create_trabajador view."""

    def setUp(self):
        self.seccion = Seccion.objects.create(numero=1)
        self.puesto = Puesto.objects.create(clave='P1')
        self.jurisdiccion = Jurisdiccion.objects.create(clave='J1')
        self.lugar = LugarAdscripcion.objects.create(nombre='L1')

    def test_create_trabajador_without_login_redirects(self):
        response = self.client.get(reverse('create_trabajador'))
        self.assertEqual(response.status_code, 302)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @patch('becas_sntsa.views.EmailMessage.send',
           side_effect=smtplib.SMTPException('fail'))
    def test_create_trabajador_email_failure_rolls_back(self, mock_send):
        """When email send fails, the user should be made active again and trabajador deleted."""
        user = User.objects.create_user(
            username='SAHM910101HDFLNA49', password='pass')
        self.client.login(username='SAHM910101HDFLNA49', password='pass')

        data = {
            'nombre': 'New',
            'apellido_paterno': 'Trabajador',
            'telefono': '1112223333',
            'correo': 'new@test.com',
            'seccion': self.seccion.id,
            'puesto': self.puesto.id,
            'jurisdiccion': self.jurisdiccion.id,
            'lugar_adscripcion': self.lugar.id,
            'talon_pago_archivo': SimpleUploadedFile("file.txt", b"x"),
        }
        response = self.client.post(reverse('create_trabajador'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Error al enviar el correo')

        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertFalse(Trabajador.objects.filter(usuario=user).exists())

FROM golang:1.22-alpine as builder

RUN apk add --no-cache musl-dev gcc
WORKDIR /go/src/github.com/ksobrenat32/scholarships-db/

COPY go.mod go.sum main.go ./
COPY code/ ./code/
RUN go mod tidy
RUN go build -ldflags "-linkmode external -extldflags -static" -o /scholarships-db

FROM alpine:3.20

COPY --from=builder /scholarships-db /

WORKDIR /app
COPY files/ ./files

RUN mkdir -p /app/uploads /app/data && \
    chown -R 1000:1000 /app && \
    chmod -R 755 /app

USER 1000
EXPOSE 8080
VOLUME [ "/app/uploads" ]
VOLUME [ "/app/data" ]

CMD ["/scholarships-db"]

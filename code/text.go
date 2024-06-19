package code

import "strings"

// Text manipulation to lower case and cleaning spaces
func UnifyText(text string) string {
	text = strings.ToLower(text)
	text = strings.TrimSpace(text)
	return text
}

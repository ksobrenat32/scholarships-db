package main

import (
	"gitlab.com/ksobrenat32/scholarships-db/code"
)

func main() {
	err := code.CreateDatabaseFile("scholarships.db")
	if err != nil {
		print(err.Error())
	}

}

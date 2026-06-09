// Command server runs the trimmed, deterministic intent-controller for the correct-shaped-lies
// experiment. It is single-process and in-memory: state lives only for the lifetime of the process,
// which is exactly what a seeded, reproducible sweep wants.
//
// Environment:
//
//	PORT            HTTP port to listen on (default 8080)
//	ML_SERVICE_URL  base URL of the Python ML service that serves /ml/evaluate (default http://127.0.0.1:8000)
package main

import (
	"log"
	"net/http"
	"os"

	"github.com/correct-shaped-lies/intent-controller/internal/controller"
)

func main() {
	port := getenv("PORT", "8080")
	mlURL := getenv("ML_SERVICE_URL", "http://127.0.0.1:8000")

	store := controller.NewStore()
	evals := controller.NewHTTPEvalClient(mlURL)
	mgr := controller.NewManager(store, evals)
	handler := controller.Router(mgr)

	addr := ":" + port
	log.Printf("intent-controller listening on %s (ml_service=%s)", addr, mlURL)
	if err := http.ListenAndServe(addr, handler); err != nil {
		log.Fatalf("server error: %v", err)
	}
}

func getenv(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}

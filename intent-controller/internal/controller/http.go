package controller

import (
	"context"
	"encoding/json"
	"net/http"
)

// Router builds the HTTP API. Go 1.22 method+path patterns; no third-party router.
func Router(m *Manager) http.Handler {
	mux := http.NewServeMux()

	mux.HandleFunc("GET /health", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	})

	mux.HandleFunc("POST /api/v1/intents", func(w http.ResponseWriter, r *http.Request) {
		var req struct {
			IntentType string                 `json:"intent_type"`
			Params     map[string]interface{} `json:"params"`
		}
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			writeErr(w, http.StatusBadRequest, err.Error())
			return
		}
		in, err := m.Create(req.IntentType, req.Params)
		if err != nil {
			writeErr(w, http.StatusBadRequest, err.Error())
			return
		}
		writeJSON(w, http.StatusCreated, in)
	})

	mux.HandleFunc("POST /api/v1/intents/{id}/process", func(w http.ResponseWriter, r *http.Request) {
		in, err := m.Process(context.Background(), r.PathValue("id"))
		if err != nil {
			writeErr(w, http.StatusNotFound, err.Error())
			return
		}
		writeJSON(w, http.StatusOK, in)
	})

	mux.HandleFunc("GET /api/v1/intents/{id}", func(w http.ResponseWriter, r *http.Request) {
		in := m.Get(r.PathValue("id"))
		if in == nil {
			writeErr(w, http.StatusNotFound, "intent not found")
			return
		}
		writeJSON(w, http.StatusOK, in)
	})

	mux.HandleFunc("GET /api/v1/intents/{id}/events", func(w http.ResponseWriter, r *http.Request) {
		events := m.Events(r.PathValue("id"))
		if events == nil {
			events = []Event{}
		}
		writeJSON(w, http.StatusOK, map[string]interface{}{"events": events})
	})

	return mux
}

func writeJSON(w http.ResponseWriter, status int, v interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func writeErr(w http.ResponseWriter, status int, msg string) {
	writeJSON(w, status, map[string]string{"error": msg})
}

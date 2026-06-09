package controller

import (
	"context"
	"testing"
)

// fakeEvals returns a fixed pass/fail per evaluator name, so we can test the allPassed gate without
// standing up the Python ML service.
type fakeEvals struct {
	passing map[string]bool
}

func (f fakeEvals) RunEval(_ context.Context, name string, threshold float64, _ *Intent) (map[string]interface{}, error) {
	passed := f.passing[name]
	score := 0.0
	if passed {
		score = 1.0
	}
	return map[string]interface{}{
		"name": name, "passed": passed, "score": score, "threshold": threshold,
		"details": map[string]interface{}{},
	}, nil
}

func runEpisode(t *testing.T, passing map[string]bool) *Intent {
	t.Helper()
	store := NewStore()
	mgr := NewManager(store, fakeEvals{passing: passing})
	in, err := mgr.Create("code_generation", map[string]interface{}{"episode_id": "ep-1"})
	if err != nil {
		t.Fatalf("create: %v", err)
	}
	if in.IntentID != "ep-1" {
		t.Fatalf("expected deterministic id ep-1, got %s", in.IntentID)
	}
	out, err := mgr.Process(context.Background(), "ep-1")
	if err != nil {
		t.Fatalf("process: %v", err)
	}
	return out
}

func TestAllPassReachesAchieved(t *testing.T) {
	out := runEpisode(t, map[string]bool{
		"correctness": true, "honesty": true, "static_safety": true, "complexity_budget": true,
	})
	if out.Status != StatusAchieved {
		t.Fatalf("expected achieved, got %s", out.Status)
	}
}

func TestAnyFailReachesFailed(t *testing.T) {
	out := runEpisode(t, map[string]bool{
		"correctness": true, "honesty": false, "static_safety": true, "complexity_budget": true,
	})
	if out.Status != StatusFailed {
		t.Fatalf("expected failed, got %s", out.Status)
	}
}

func TestTrajectoryEventsAreOrderedAndLogical(t *testing.T) {
	store := NewStore()
	mgr := NewManager(store, fakeEvals{passing: map[string]bool{
		"correctness": true, "honesty": true, "static_safety": true, "complexity_budget": true,
	}})
	mgr.Create("code_generation", map[string]interface{}{"episode_id": "ep-2"})
	mgr.Process(context.Background(), "ep-2")

	events := mgr.Events("ep-2")
	if len(events) == 0 {
		t.Fatal("no events emitted")
	}
	// Logical clock is strictly increasing across the episode.
	for i := 1; i < len(events); i++ {
		if events[i].TsLogical <= events[i-1].TsLogical {
			t.Fatalf("ts_logical not strictly increasing at %d: %d <= %d", i, events[i].TsLogical, events[i-1].TsLogical)
		}
	}
	// The terminal state_change is to achieved.
	last := events[len(events)-1]
	if last.EventType != "state_change" || last.ToStatus == nil || *last.ToStatus != string(StatusAchieved) {
		t.Fatalf("expected final state_change to achieved, got %+v", last)
	}
}

func TestInvalidTransitionRejected(t *testing.T) {
	if IsValidTransition(StatusDeclared, StatusAchieved) {
		t.Fatal("declared -> achieved should be invalid")
	}
	if !IsValidTransition(StatusVerifying, StatusAchieved) {
		t.Fatal("verifying -> achieved should be valid")
	}
}

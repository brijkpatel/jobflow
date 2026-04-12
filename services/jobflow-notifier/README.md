# jobflow-notifier

Go service. Kafka consumer → Resend API. Sends email notifications for all application lifecycle events.

## Run
```bash
docker compose -f ../../infrastructure/docker/docker-compose.dev.yml up -d
go run ./cmd/notifier
```

## Test
```bash
go test ./...
go test -run Integration ./...
```

## Structure
- `internal/domain/` — Notification entity, NotificationTemplate interface
- `internal/application/` — SendNotificationUseCase
- `internal/infrastructure/kafka/` — Kafka consumer (application-events, match-events)
- `internal/infrastructure/resend/` — Resend API client
- `internal/infrastructure/templates/` — Go HTML email templates per event type

## Protocols
- **Consumes:** Kafka `application-events` (status changes: submitted, accepted, rejected, interview)
- **Consumes:** Kafka `match-events` (new match found for user)
- **No outbound calls beyond Resend**

## Event → email mapping
| Event | Email |
|-------|-------|
| `application.submitted` | "Your application to {company} has been submitted" |
| `application.interview` | "Interview prep ready for {company}" |
| `application.accepted` | "Offer received from {company}" |
| `application.rejected` | "Update on your {company} application" |
| `match.found` | "{N} new jobs matched your profile" (batched, max 1/day) |
| `hitl.approval_required` | "Review your application before submission" |

## Key rules
- Written in Go — only service not in Python (email sending does not need ADK/LLM)
- Match notifications are batched: at most 1 digest email per user per day
- KEDA scales on combined consumer lag across both topics (min 0, max 3)
- Resend API key in Kubernetes Secret, not ConfigMap
- See `.claude/architecture.md` for Kafka event schemas

"""Generate a synthetic distractor pack so catalog-size scaling can go past the ~30
real public tools (to 50 / 100 / 200+). Every server is prefixed `syn-` and the file
is flagged `synthetic: true`, so results can be split real-vs-synthetic later.

Some packs deliberately overlap real servers' intents (internal docs search, code
search, flight booking) to act as hard negatives.

    python scripts/make_distractors.py  ->  data/catalog/distractors_synthetic.json
"""

import json
from pathlib import Path

PACKS: dict[str, tuple[str, list[tuple[str, str]]]] = {
    "syn-tickets": (
        "Issue tracker for engineering work",
        [
            ("create_issue", "Create a new issue with title, description, assignee and labels."),
            ("search_issues", "Search issues by JQL-like query, status, assignee or label."),
            ("get_issue", "Get one issue with comments and history by key."),
            ("transition_issue", "Move an issue to another workflow status."),
            ("add_comment", "Add a comment to an issue."),
            ("list_sprints", "List active and upcoming sprints for a board."),
            ("link_issues", "Link two issues (blocks, relates, duplicates)."),
        ],
    ),
    "syn-chat": (
        "Team chat workspace",
        [
            ("post_message", "Post a message to a channel or thread."),
            ("search_messages", "Full-text search over channel messages."),
            ("list_channels", "List public and private channels you can see."),
            ("get_thread", "Fetch all replies in a message thread."),
            ("add_reaction", "Add an emoji reaction to a message."),
            ("set_status", "Set the user's chat status and emoji."),
        ],
    ),
    "syn-crm": (
        "Customer relationship management",
        [
            ("search_accounts", "Find customer accounts by name, domain or owner."),
            ("get_opportunity", "Get an opportunity with stage, amount and close date."),
            ("update_opportunity_stage", "Change an opportunity's pipeline stage."),
            ("log_activity", "Log a call, meeting or email against a contact."),
            ("list_contacts", "List contacts for an account."),
            ("forecast_summary", "Summarize the sales forecast for a quarter."),
        ],
    ),
    "syn-warehouse": (
        "Cloud data warehouse",
        [
            ("run_sql", "Execute a read-only SQL query and return rows."),
            ("list_tables", "List tables and views in a schema."),
            ("describe_table", "Show columns, types and comments for a table."),
            ("query_history", "List recent queries with runtime and credits used."),
            ("explain_query", "Return the query plan for a SQL statement."),
        ],
    ),
    "syn-wiki": (
        "Internal company wiki and knowledge base",
        [
            ("search_pages", "Search internal wiki pages and runbooks by keyword."),
            ("get_page", "Fetch an internal wiki page as markdown."),
            ("create_page", "Create a new wiki page in a space."),
            ("list_spaces", "List wiki spaces you have access to."),
            ("page_history", "Show the edit history of a wiki page."),
        ],
    ),
    "syn-codehost": (
        "Internal source code hosting",
        [
            ("search_code", "Search code across internal repositories."),
            ("get_file", "Read a file from a repository at a ref."),
            ("list_pull_requests", "List open pull requests for a repo."),
            ("create_pull_request", "Open a pull request from a branch."),
            ("get_build_status", "Get CI build status for a commit."),
            ("list_branches", "List branches in a repository."),
        ],
    ),
    "syn-calendar": (
        "Calendar and scheduling",
        [
            ("list_events", "List calendar events in a time range."),
            ("create_event", "Create a meeting with attendees and a video link."),
            ("find_free_slots", "Find common free time for several people."),
            ("cancel_event", "Cancel an event and notify attendees."),
            ("rsvp", "Accept, decline or tentatively accept an invite."),
        ],
    ),
    "syn-mail": (
        "Email",
        [
            ("search_mail", "Search the mailbox with a query."),
            ("send_mail", "Send an email to recipients."),
            ("draft_mail", "Create an email draft without sending."),
            ("get_message", "Get a full email message with attachments list."),
            ("archive_thread", "Archive an email thread."),
        ],
    ),
    "syn-storage": (
        "Cloud file storage",
        [
            ("search_files", "Search files and folders by name or content."),
            ("read_file", "Read the text content of a stored file."),
            ("upload_file", "Upload a file to a folder."),
            ("share_file", "Share a file with people and set permissions."),
            ("list_folder", "List items in a folder."),
        ],
    ),
    "syn-hr": (
        "HR and people system",
        [
            ("get_employee", "Look up an employee's profile, manager and team."),
            ("request_leave", "Submit a leave request."),
            ("leave_balance", "Show remaining leave balance."),
            ("org_chart", "Return the reporting chain for a person."),
            ("list_holidays", "List public holidays for an office location."),
        ],
    ),
    "syn-finance": (
        "Expense and invoice management",
        [
            ("submit_expense", "Submit an expense with receipt and category."),
            ("list_invoices", "List invoices by vendor, status or date."),
            ("approve_expense", "Approve or reject a pending expense."),
            ("get_budget", "Get budget vs actual for a cost center."),
            ("currency_convert", "Convert an amount between currencies at today's rate."),
        ],
    ),
    "syn-monitoring": (
        "Observability and alerting",
        [
            ("query_metrics", "Query a time series metric with filters."),
            ("search_logs", "Search application logs by service, level and text."),
            ("list_alerts", "List firing alerts."),
            ("ack_alert", "Acknowledge an alert."),
            ("get_trace", "Fetch a distributed trace by ID."),
            ("list_dashboards", "List monitoring dashboards."),
        ],
    ),
    "syn-incident": (
        "Incident management",
        [
            ("declare_incident", "Declare an incident with severity and commander."),
            ("update_incident", "Post a status update to an incident."),
            ("list_incidents", "List open and recent incidents."),
            ("get_oncall", "Who is on call for a service right now."),
            ("write_postmortem", "Create a postmortem document from an incident."),
        ],
    ),
    "syn-travel": (
        "Corporate travel booking",
        [
            ("search_flights", "Search corporate-policy flights between cities on dates."),
            ("book_flight", "Book a selected flight on the corporate card."),
            ("search_hotels", "Search policy-compliant hotels near a location."),
            ("get_itinerary", "Get an employee's upcoming trip itinerary."),
            ("cancel_booking", "Cancel a travel booking."),
        ],
    ),
    "syn-kb-search": (
        "Vector search over uploaded documents",
        [
            ("semantic_search", "Semantic search over your uploaded document corpus."),
            ("ingest_document", "Chunk and embed a document into the index."),
            ("list_collections", "List vector collections."),
            ("delete_collection", "Delete a vector collection."),
        ],
    ),
    "syn-web": (
        "General web access",
        [
            ("web_search", "Search the public web and return top results with snippets."),
            ("fetch_url", "Fetch a web page and return readable text."),
            ("screenshot_url", "Take a screenshot of a web page."),
        ],
    ),
    "syn-design": (
        "Design files",
        [
            ("get_design_file", "Get frames and components in a design file."),
            ("export_frame", "Export a frame as PNG or SVG."),
            ("list_comments", "List comments on a design file."),
            ("get_variables", "Get design tokens and variables."),
        ],
    ),
    "syn-market": (
        "Market data",
        [
            ("get_quote", "Latest price quote for a stock ticker."),
            ("get_ohlc", "OHLC candles for a ticker and interval."),
            ("company_filings", "List recent regulatory filings for a company."),
            ("earnings_calendar", "Upcoming earnings dates."),
            ("fx_rate", "Spot FX rate between two currencies."),
        ],
    ),
    "syn-cloudops": (
        "Cloud infrastructure operations",
        [
            ("list_instances", "List compute instances with state and region."),
            ("restart_instance", "Restart a compute instance."),
            ("get_cost_report", "Cloud spend by service for a period."),
            ("list_buckets", "List object storage buckets."),
            ("describe_iam_role", "Describe an IAM role and its policies."),
            ("deploy_stack", "Deploy an infrastructure-as-code stack."),
        ],
    ),
    "syn-notes": (
        "Personal notes",
        [
            ("create_note", "Create a note."),
            ("search_notes", "Search notes by text."),
            ("append_to_note", "Append text to an existing note."),
        ],
    ),
    "syn-weather": (
        "Weather",
        [
            ("current_weather", "Current weather for a city."),
            ("forecast", "Multi-day forecast for a location."),
        ],
    ),
    "syn-maps": (
        "Maps and places",
        [
            ("search_places", "Find places by query near a location."),
            ("directions", "Driving, walking or transit directions."),
            ("geocode", "Convert an address to coordinates."),
        ],
    ),
    "syn-ml-registry": (
        "Internal ML model registry",
        [
            ("search_models", "Search registered models by name, task or owner."),
            ("get_model_version", "Get metrics and artifacts for a model version."),
            ("promote_model", "Promote a model version to staging or production."),
            ("list_experiments", "List experiment runs with metrics."),
        ],
    ),
}


def main() -> None:
    servers = {
        name: {
            "description": desc,
            "tools": [
                {"name": t, "description": d, "input_schema": {"type": "object"}} for t, d in tools
            ],
        }
        for name, (desc, tools) in PACKS.items()
    }
    out = {"synthetic": True, "servers": servers}
    path = Path(__file__).resolve().parents[1] / "data" / "catalog" / "distractors_synthetic.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2))
    n = sum(len(s["tools"]) for s in servers.values())
    print(f"wrote {n} synthetic tools across {len(servers)} servers -> {path}")


if __name__ == "__main__":
    main()

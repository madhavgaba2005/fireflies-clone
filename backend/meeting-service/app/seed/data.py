"""Seed catalogue: seven meetings at Northwind, a (fictional) company building Routewise, a route
planning product for delivery fleets. People and story threads recur across meetings (the bulk
import fix, the Brightline pilot, the senior backend hire) so filters and search have real data.

Transcript lines are (speaker first name, text). Timestamps are derived from word counts by the
loader, so outline chapters and action items reference a line index instead of a hard-coded time.
"""

from dataclasses import dataclass, field

PEOPLE: dict[str, str] = {
    "Priya Sharma": "priya.sharma@northwind.io",
    "Arjun Mehta": "arjun.mehta@northwind.io",
    "Sarah Chen": "sarah.chen@northwind.io",
    "Elena Rodriguez": "elena.rodriguez@northwind.io",
    "David Kim": "david.kim@northwind.io",
    "Noah Williams": "noah.williams@northwind.io",
    "Marcus Johnson": "marcus.johnson@northwind.io",
    "Aisha Patel": "aisha.patel@northwind.io",
    "Kenji Tanaka": "kenji.tanaka@northwind.io",
    "Tom Becker": "tom.becker@brightline-logistics.com",
    "Laura Bennett": "laura.bennett@brightline-logistics.com",
}


@dataclass(frozen=True)
class SeedTopic:
    title: str
    summary: str
    line: int


@dataclass(frozen=True)
class SeedActionItem:
    title: str
    assignee: str | None  # first name of a participant
    line: int
    due_in_days: int | None = None
    completed: bool = False


@dataclass(frozen=True)
class SeedMeeting:
    title: str
    days_ago: int
    time: tuple[int, int]  # UTC hour, minute
    participants: list[str]
    lines: list[tuple[str, str]]
    overview: str
    keywords: list[str]
    topics: list[SeedTopic]
    action_items: list[SeedActionItem] = field(default_factory=list)


MEETINGS: list[SeedMeeting] = [
    SeedMeeting(
        title="Weekly Product Sync",
        days_ago=1,
        time=(10, 0),
        participants=["Priya Sharma", "Arjun Mehta", "Sarah Chen", "Elena Rodriguez"],
        lines=[
            (
                "Priya",
                "Morning everyone. Let's keep this to thirty minutes. Agenda is the 2.4 release status, the onboarding checklist numbers, design QA for the new route planner, and launch comms. Arjun, do you want to start with the release?",
            ),
            (
                "Arjun",
                "Sure. Release 2.4 is feature complete as of yesterday. We have eleven open bugs and two of them are blockers. Both blockers are in the bulk route import: when a CSV has more than five thousand stops, the import times out.",
            ),
            ("Priya", "Is that a regression, or did it never work at that size?"),
            (
                "Arjun",
                "It never worked at that size, but we promised Brightline-sized customers it would. David thinks it's the geocoding calls being made one after another. He's moving them into a batched job, which should cut the import from minutes to seconds.",
            ),
            (
                "Sarah",
                "Does the batched job change the UI at all? Right now the import modal just shows a spinner.",
            ),
            (
                "Arjun",
                "It will. The import becomes asynchronous, so the user gets a progress bar and a notification when it finishes. That's actually a better experience for big files.",
            ),
            (
                "Sarah",
                "Then I need to design the progress state and the partial failure state. What happens if forty stops out of five thousand fail to geocode?",
            ),
            (
                "Arjun",
                "We'd import everything that succeeded and give them a downloadable list of the failures, with the reason for each one.",
            ),
            (
                "Sarah",
                "Okay. I'll have mocks for the progress and partial failure states by Wednesday so Noah isn't blocked.",
            ),
            ("Priya", "Great. Arjun, is the release date still Thursday the sixteenth?"),
            (
                "Arjun",
                "I'd rather say Monday the twentieth. If the batching change lands Tuesday, I want two full days of regression testing on the import path. I don't want to ship a timeout fix that breaks small imports.",
            ),
            ("Priya", "I'm fine with Monday. Elena, does that move anything on your side?"),
            (
                "Elena",
                "It moves the announcement email, which was scheduled for the seventeenth. Moving it to the twenty-first is actually better, Tuesdays have our best open rates. I'll update the campaign calendar today.",
            ),
            (
                "Priya",
                "Perfect. Next, the onboarding checklist. We shipped the new checklist three weeks ago. Elena, you have the numbers?",
            ),
            (
                "Elena",
                "I do. Activation, which we define as a customer creating and dispatching their first route within seven days, went from thirty-eight percent to fifty-one percent. That's the biggest jump we've seen from a single change.",
            ),
            ("Arjun", "That's huge. Do we know which step drives it?"),
            (
                "Elena",
                "The import your stops step. People who complete it activate at almost eighty percent. People who skip it are still at around thirty.",
            ),
            (
                "Priya",
                "So the import fix matters even more than we thought. If large customers hit the timeout during onboarding, they never activate.",
            ),
            (
                "Sarah",
                "Should we add a sample data option to that step? Some trial users don't have a clean CSV ready on day one.",
            ),
            (
                "Priya",
                "I like that. Let's scope it for 2.5, not 2.4. Sarah, can you write a short proposal with the sample dataset idea?",
            ),
            ("Sarah", "Yes, I'll put it in the product doc by the end of next week."),
            ("Priya", "Third item, design QA for the route planner. Sarah, where are we?"),
            (
                "Sarah",
                "Mostly good, three issues. The drag handles on stops are too small on tablets, the colour for delayed routes fails contrast in dark mode, and the map legend overlaps the zoom controls on smaller laptops.",
            ),
            (
                "Arjun",
                "The legend one is quick. The drag handles need a bigger touch target, which touches the shared list component, so I'd rather do that carefully.",
            ),
            (
                "Priya",
                "Let's fix the legend and the contrast in 2.4, and do the touch targets in 2.5 with proper testing.",
            ),
            ("Sarah", "Agreed. I'll file all three with screenshots today."),
            ("Priya", "Last item, launch comms. Elena?"),
            (
                "Elena",
                "For 2.4 we have the email, a short changelog post, and an in-app banner. The banner points to a two-minute video of the bulk import, so I need a stable build to record it.",
            ),
            (
                "Arjun",
                "The staging build from Friday should be stable enough for recording. I'll send you the link and a test account after this call.",
            ),
            (
                "Priya",
                "Good. To recap: the release moves to Monday the twentieth, the email moves to the twenty-first, Sarah delivers the import mocks Wednesday, and the legend and contrast fixes go into 2.4. Thanks everyone.",
            ),
        ],
        overview=(
            "The team reviewed release 2.4. Bulk route import times out above five thousand stops "
            "because geocoding runs sequentially; David is batching it, which also makes imports "
            "asynchronous with a progress bar. To allow two days of regression testing, the release "
            "moves from Thursday the 16th to Monday the 20th and the announcement email to Tuesday "
            "the 21st. The new onboarding checklist lifted 7-day activation from 38% to 51%, driven "
            "by the stop-import step, which makes the import fix even more important. Design QA "
            "found three route-planner issues: the legend overlap and dark-mode contrast are fixed in "
            "2.4, tablet touch targets move to 2.5."
        ),
        keywords=[
            "Release 2.4",
            "Bulk import",
            "Geocoding",
            "Activation",
            "Design QA",
            "Launch email",
        ],
        topics=[
            SeedTopic(
                "Release 2.4 status and import timeouts",
                "Two blockers in bulk import above 5,000 stops. Geocoding is being batched into an async job with progress and a failure report; release moves to Monday the 20th.",
                1,
            ),
            SeedTopic(
                "Onboarding checklist results",
                "Seven-day activation rose from 38% to 51%. Users who complete the stop-import step activate at ~80%; a sample-data option is proposed for 2.5.",
                13,
            ),
            SeedTopic(
                "Route planner design QA",
                "Three issues: tablet drag handles, dark-mode contrast for delayed routes, legend overlapping zoom controls. Legend and contrast ship in 2.4.",
                21,
            ),
            SeedTopic(
                "Launch communications",
                "Email, changelog post and in-app banner linking to a bulk-import video recorded on Friday's staging build.",
                26,
            ),
        ],
        action_items=[
            SeedActionItem(
                "Deliver mocks for the import progress and partial-failure states", "Sarah", 8, 2
            ),
            SeedActionItem(
                "Land the batched geocoding fix and run two days of import regression tests",
                "Arjun",
                10,
                4,
            ),
            SeedActionItem(
                "Move the 2.4 announcement email to Tuesday the 21st", "Elena", 12, completed=True
            ),
            SeedActionItem(
                "Write a proposal for a sample-data option in the onboarding import step",
                "Sarah",
                20,
                8,
            ),
            SeedActionItem(
                "File the three route-planner design QA issues with screenshots",
                "Sarah",
                25,
                completed=True,
            ),
            SeedActionItem(
                "Send Elena the staging link and a test account for the demo video", "Arjun", 28, 0
            ),
        ],
    ),
    SeedMeeting(
        title="Engineering Sprint 14 Review",
        days_ago=3,
        time=(15, 0),
        participants=["Arjun Mehta", "David Kim", "Noah Williams", "Priya Sharma"],
        lines=[
            (
                "Arjun",
                "Okay, let's get started. Sprint fourteen review. We committed to thirty-four points and closed twenty-nine. The five we carried over are the webhook retry work, which I'll explain in a minute. David, do you want to demo the geocoding change first?",
            ),
            (
                "David",
                "Sure. Before this change, every stop in an import made its own call to the geocoding provider, one after another. For a five-thousand-stop file that's five thousand round trips, roughly eleven minutes. Now we group stops into batches of two hundred and run up to eight batches in parallel.",
            ),
            ("Priya", "And what's the time now for the same file?"),
            (
                "David",
                "Fifty-two seconds on staging. And the request no longer blocks. The import is a background job, the API returns a job id immediately, and the client polls for progress.",
            ),
            (
                "Noah",
                "I've already wired the progress bar to the job endpoint using Sarah's interim design. When her final mocks land it's mostly styling.",
            ),
            (
                "Priya",
                "What about rate limits on the provider side? Eight parallel batches sounds aggressive.",
            ),
            (
                "David",
                "Their limit is fifty requests per second on our plan, and we peak around thirty-two. I also added exponential backoff when we get a 429, capped at five retries per batch.",
            ),
            ("Arjun", "And failed rows end up in the failure report, not silently dropped?"),
            (
                "David",
                "Correct. Each failed stop is written with the reason, and the report is downloadable as a CSV from the import summary.",
            ),
            ("Arjun", "Nice. Noah, frontend performance next."),
            (
                "Noah",
                "The route list was re-rendering every row whenever the map moved. With a thousand stops the page dropped to about twelve frames per second. I virtualized the list, so we only render what's on screen, and memoized the row component.",
            ),
            (
                "Noah",
                "Now it holds sixty frames per second with ten thousand stops on my laptop, and the initial render went from 1.8 seconds to about three hundred milliseconds.",
            ),
            ("Priya", "That's a big difference. Does it change anything for keyboard users?"),
            (
                "Noah",
                "Good question. Virtualization can break focus when a row scrolls out of view. I kept focus management working for the arrow keys, but I haven't tested with a screen reader yet.",
            ),
            (
                "Arjun",
                "Let's not merge until that's tested. Noah, can you do a VoiceOver and NVDA pass before Thursday?",
            ),
            ("Noah", "Yes, I'll do both and write up anything I find."),
            (
                "Arjun",
                "Now the incident. Last Tuesday a customer's webhook endpoint was down for about forty minutes and we dropped every route-completed event in that window. They found out from their drivers, not from us.",
            ),
            (
                "David",
                "The root cause is simple: we only try a webhook once. If it fails, we log it and move on.",
            ),
            (
                "Arjun",
                "So the carried-over work is a proper retry policy. Retries with backoff over twenty-four hours, then a dead-letter list the customer can see and replay from settings.",
            ),
            (
                "Priya",
                "How confident are we in finishing that next sprint? This customer asked for a date.",
            ),
            (
                "David",
                "The retry queue is two or three days. The customer-facing replay screen is the uncertain part, because it needs design.",
            ),
            (
                "Priya",
                "Then let's tell them retries ship next sprint and the replay screen the sprint after. I'd rather give a date we can hit. I'll email their account manager today.",
            ),
            (
                "Arjun",
                "Agreed. I'll write the incident postmortem by Wednesday so we can share a cleaned-up version with them.",
            ),
            (
                "Arjun",
                "Last thing, next sprint priorities. In order: webhook retries, import failure report polish, the accessibility pass on the route list, and the two remaining 2.4 bugs.",
            ),
            (
                "Noah",
                "Could we add the flaky end-to-end tests? We've had to rerun CI on almost every pull request this week.",
            ),
            (
                "Arjun",
                "Yes, that's costing everyone time. David, would you take the first look? I suspect the test database isn't being reset between specs.",
            ),
            ("David", "I can look on Friday. If it is the reset, it's a small fix."),
            (
                "Arjun",
                "Great. Velocity is fine, the geocoding work is a real win, and the incident gave us a clear priority. Thanks all.",
            ),
        ],
        overview=(
            "Sprint 14 closed 29 of 34 points; webhook retries carried over. David demoed batched "
            "geocoding: a 5,000-stop import dropped from about eleven minutes to 52 seconds and now "
            "runs as a background job with progress, backoff on rate limits and a CSV failure report. "
            "Noah virtualized the route list (12 → 60 fps with 10k stops) but it needs a screen-reader "
            "pass before merging. A webhook outage dropped a customer's events because webhooks are "
            "tried only once; retries with a dead-letter list are the top priority next sprint, with a "
            "postmortem by Wednesday."
        ),
        keywords=[
            "Sprint 14",
            "Geocoding",
            "Background jobs",
            "Virtualization",
            "Webhooks",
            "Postmortem",
        ],
        topics=[
            SeedTopic(
                "Sprint 14 outcomes", "29 of 34 points closed; webhook retry work carried over.", 0
            ),
            SeedTopic(
                "Batched geocoding demo",
                "Import time for 5,000 stops fell from ~11 minutes to 52 seconds using parallel batches, backoff on 429s and a downloadable failure report.",
                1,
            ),
            SeedTopic(
                "Route list performance",
                "Virtualization and memoization raised the list from 12 to 60 fps; accessibility testing is required before merge.",
                10,
            ),
            SeedTopic(
                "Webhook incident and retry plan",
                "Single-attempt webhooks dropped 40 minutes of events. Plan: retries over 24 hours plus a replayable dead-letter list.",
                16,
            ),
            SeedTopic(
                "Next sprint priorities",
                "Webhook retries, failure report polish, accessibility pass, remaining 2.4 bugs, and the flaky end-to-end tests.",
                23,
            ),
        ],
        action_items=[
            SeedActionItem(
                "Run a VoiceOver and NVDA pass on the virtualized route list", "Noah", 14, 1
            ),
            SeedActionItem(
                "Implement webhook retries with backoff and a dead-letter list", "David", 18, 10
            ),
            SeedActionItem(
                "Email the customer's account manager with the webhook retry timeline",
                "Priya",
                21,
                completed=True,
            ),
            SeedActionItem("Write the webhook incident postmortem", "Arjun", 22, 1),
            SeedActionItem(
                "Investigate flaky end-to-end tests (test database reset)", "David", 26, 2
            ),
        ],
    ),
    SeedMeeting(
        title="Discovery Call — Brightline Logistics",
        days_ago=5,
        time=(16, 30),
        participants=["Marcus Johnson", "Priya Sharma", "Tom Becker", "Laura Bennett"],
        lines=[
            (
                "Marcus",
                "Tom, Laura, thanks for making the time. Our goal today is to understand how dispatch works at Brightline right now and where it hurts, and then show you anything relevant. Tom, could you start with the big picture?",
            ),
            (
                "Tom",
                "Sure. We run about three hundred and forty trucks out of six depots in the Midwest, mostly regional deliveries for retail and grocery. Each depot has two or three dispatchers who build routes every evening for the next day.",
            ),
            ("Priya", "How do they build them today?"),
            (
                "Tom",
                "Honestly, a mix of an old on-premise routing tool and spreadsheets. The tool gives a first draft, then dispatchers spend about two hours adjusting it by hand, because it doesn't know about dock appointment windows or which drivers can handle refrigerated loads.",
            ),
            ("Priya", "So the constraints live in the dispatchers' heads, not in the system."),
            (
                "Tom",
                "Exactly. When one of our senior dispatchers was out for three weeks last spring, on-time delivery at that depot dropped from ninety-four to eighty-seven percent.",
            ),
            ("Marcus", "That's a real cost. What does a late delivery mean for you contractually?"),
            (
                "Tom",
                "Two of our largest grocery customers have penalties. A missed window costs us between two and five hundred dollars per stop, plus the damage to the relationship.",
            ),
            (
                "Laura",
                "From the IT side, my concern is integration. Our orders come from an Oracle-based order management system, and the drivers use handhelds with our own app. Anything new has to get orders in automatically and push routes out to those devices.",
            ),
            (
                "Priya",
                "We have a REST API and webhooks for exactly that. Orders can be pushed to us or pulled on a schedule, and finished routes are sent out as webhook events your driver app can consume.",
            ),
            (
                "Laura",
                "What about volumes? On a peak day before the holidays we're at about six thousand stops across all depots.",
            ),
            (
                "Priya",
                "We just finished work on large imports. Six thousand stops now import in about a minute, and the API handles that volume comfortably.",
            ),
            (
                "Laura",
                "And single sign-on? We're on Azure AD, and I won't approve another separate password for dispatchers.",
            ),
            (
                "Marcus",
                "SSO with Azure AD is included in our enterprise plan, using SAML. I can send you the setup guide.",
            ),
            (
                "Laura",
                "Please do. I'll also need your SOC 2 report and a data processing agreement before anything goes to procurement.",
            ),
            ("Marcus", "Of course. I'll send the SOC 2 Type II report and our standard DPA today."),
            (
                "Tom",
                "Can your system actually handle the dock windows and the refrigerated-driver rule? That's what matters most to my dispatchers.",
            ),
            (
                "Priya",
                "Both are standard constraints in our planner: time windows per stop and skills per driver and vehicle. The planner will never assign a refrigerated load to a driver without that skill.",
            ),
            ("Tom", "Then I'd like to see it with our data, not a demo dataset."),
            (
                "Marcus",
                "That's exactly what I'd suggest. We run a two-week pilot at one depot. You send us a week of historical orders, we load them, and your dispatchers compare our routes with what they actually ran.",
            ),
            (
                "Tom",
                "The Columbus depot would be the right place. It's mid-sized and the team there is open to change.",
            ),
            (
                "Laura",
                "I'm fine with a pilot if the data is anonymized. No customer names, and no addresses beyond what's needed for routing.",
            ),
            (
                "Priya",
                "We can work with depot-level addresses and hashed identifiers for everything else. I'll write up the data requirements so your team knows exactly what to export.",
            ),
            (
                "Marcus",
                "For next steps, let's book a technical session with Laura and our solutions engineer to walk through the API and SSO, and a pilot kickoff with the Columbus team.",
            ),
            (
                "Tom",
                "Works for me. Ideally the pilot starts before the holiday peak, so the first week of November at the latest.",
            ),
            (
                "Marcus",
                "Understood. I'll send a few slots for both sessions by tomorrow, and a short pilot proposal with success criteria, on-time percentage and planning hours saved, by the end of the week.",
            ),
            ("Tom", "Great. Thanks, this was useful."),
        ],
        overview=(
            "Brightline Logistics runs ~340 trucks from six Midwest depots. Dispatchers spend about two "
            "hours each evening hand-adjusting routes because their current tool ignores dock windows "
            "and refrigerated-driver rules; when a senior dispatcher was away, on-time delivery fell "
            "from 94% to 87%, and missed windows cost $200–500 per stop. IT requires automated order "
            "import from their Oracle OMS, routes pushed to driver handhelds, Azure AD SSO, a SOC 2 "
            "report and a DPA. Both sides agreed on a two-week pilot at the Columbus depot using "
            "anonymized historical orders, starting before the holiday peak."
        ),
        keywords=[
            "Brightline Logistics",
            "Dispatch",
            "Time windows",
            "Integration",
            "SSO",
            "Pilot",
        ],
        topics=[
            SeedTopic(
                "Brightline's current dispatch process",
                "Six depots, evening route building in a legacy tool plus spreadsheets, ~2 hours of manual adjustment per dispatcher.",
                1,
            ),
            SeedTopic(
                "Business impact of late deliveries",
                "On-time rate dropped to 87% without a senior dispatcher; grocery contracts penalize missed windows at $200–500 per stop.",
                5,
            ),
            SeedTopic(
                "Integration, volume and security requirements",
                "Oracle OMS order import, webhooks to driver handhelds, 6,000-stop peak days, Azure AD SSO, SOC 2 and DPA.",
                8,
            ),
            SeedTopic(
                "Pilot proposal at the Columbus depot",
                "Two-week pilot comparing planner routes with a week of anonymized historical orders.",
                18,
            ),
            SeedTopic(
                "Next steps",
                "Technical session on API and SSO, pilot kickoff, proposal with success criteria; start by early November.",
                23,
            ),
        ],
        action_items=[
            SeedActionItem(
                "Send the Azure AD SAML setup guide to Laura", "Marcus", 13, completed=True
            ),
            SeedActionItem(
                "Send the SOC 2 Type II report and standard DPA", "Marcus", 15, completed=True
            ),
            SeedActionItem(
                "Write the pilot data requirements (anonymized export spec)", "Priya", 22, 3
            ),
            SeedActionItem(
                "Send slots for the technical session and the pilot kickoff",
                "Marcus",
                25,
                completed=True,
            ),
            SeedActionItem("Send the pilot proposal with success criteria", "Marcus", 25, 1),
        ],
    ),
    SeedMeeting(
        title="Route Planner Mobile Redesign — Design Review",
        days_ago=8,
        time=(13, 0),
        participants=["Sarah Chen", "Noah Williams", "Priya Sharma"],
        lines=[
            (
                "Sarah",
                "Thanks for joining. Today I want feedback on the mobile redesign of the route planner, mainly the stop list, the route summary card, and how drivers report a problem at a stop. I'll share my screen.",
            ),
            (
                "Sarah",
                "First, the stop list. Today drivers see every stop with full details, which is a lot of scrolling. In the new version each stop collapses to one line: sequence number, customer, time window, and a status dot. Tapping expands it.",
            ),
            ("Priya", "I like it. What does the status dot show?"),
            (
                "Sarah",
                "Green for on time, amber when the predicted arrival is within fifteen minutes of the window closing, and red when we expect to miss it.",
            ),
            (
                "Noah",
                "Is the prediction available on the device, or does it need a server call every time?",
            ),
            ("Sarah", "That's my question for you. Ideally it updates as the driver moves."),
            (
                "Noah",
                "We already get the ETA from the server every two minutes for the dispatcher view. We can push the same value to the app. Computing it on the device would drain the battery and duplicate logic.",
            ),
            ("Priya", "Two-minute updates are fine for drivers. Let's reuse the server value."),
            (
                "Sarah",
                "Great. Second, the route summary card at the top: stops remaining, distance, and expected finish time. In testing, drivers told us the finish time is what they actually care about.",
            ),
            ("Priya", "Did you test with drivers directly?"),
            (
                "Sarah",
                "Yes, six drivers at two customers. Four of them said they currently text their dispatcher to ask when they'll be done. Showing the finish time could cut a lot of those messages.",
            ),
            (
                "Noah",
                "Visually, the card takes about a third of the screen on smaller phones. Could it shrink when the list scrolls?",
            ),
            (
                "Sarah",
                "Good idea. A collapsed state with just the finish time that expands when you scroll back up. I'll prototype that.",
            ),
            (
                "Sarah",
                "Third, reporting a problem. Today it's three screens deep. My proposal is a long-press on a stop that opens a sheet with the five most common problems: customer closed, no access, damaged goods, refused delivery, and other.",
            ),
            ("Priya", "Long-press isn't very discoverable. Some drivers will never find it."),
            (
                "Sarah",
                "Fair. What if there's also a visible report issue button inside the expanded stop, and long-press is the shortcut?",
            ),
            ("Priya", "That works, as long as both paths open the same sheet."),
            ("Noah", "For damaged goods we'll want a photo. Is the camera in scope?"),
            (
                "Sarah",
                "Yes. An optional photo for every problem type, required for damaged goods. Customers keep asking for proof.",
            ),
            (
                "Noah",
                "Photos on bad cell connections worry me. We should queue uploads and retry in the background, otherwise drivers get stuck on a spinner.",
            ),
            (
                "Priya",
                "Agreed. Offline-first for the report: it saves locally immediately and the photo uploads when there's signal.",
            ),
            (
                "Noah",
                "I'll write a short technical note on the upload queue, including how we show pending uploads to the driver.",
            ),
            (
                "Sarah",
                "Last thing, accessibility. I've checked contrast on all three screens and the tap targets are at least forty-eight pixels. I haven't tested with large system fonts yet.",
            ),
            (
                "Noah",
                "I can test with the largest font setting on both platforms when I build the first screen.",
            ),
            (
                "Priya",
                "This is strong work, Sarah. Let's aim for a clickable prototype of all three flows next week and put it in front of the same six drivers.",
            ),
            (
                "Sarah",
                "Will do. I'll update the prototype with the collapsing card and the report button and schedule the driver sessions.",
            ),
        ],
        overview=(
            "Sarah presented the mobile route planner redesign. Stops collapse to one line with a "
            "colour-coded status dot driven by the server ETA (refreshed every two minutes, not "
            "computed on the device). The summary card leads with expected finish time — four of six "
            "drivers interviewed text dispatch to ask — and will collapse while scrolling. Problem "
            "reporting moves from three screens to a sheet opened by a visible button or a long-press, "
            "with photos required for damaged goods and an offline-first upload queue. Next: a "
            "clickable prototype tested with the same six drivers."
        ),
        keywords=[
            "Mobile redesign",
            "Stop list",
            "ETA",
            "Problem reporting",
            "Offline upload",
            "Accessibility",
        ],
        topics=[
            SeedTopic(
                "Collapsed stop list with status",
                "One-line stops with green/amber/red status based on the predicted arrival versus the time window.",
                1,
            ),
            SeedTopic(
                "ETA source for status",
                "Reuse the server ETA pushed every two minutes instead of computing on the device.",
                4,
            ),
            SeedTopic(
                "Route summary card",
                "Finish time is what drivers want; the card collapses while scrolling on small phones.",
                8,
            ),
            SeedTopic(
                "Reporting a problem at a stop",
                "One sheet with five common problems, reachable by button or long-press; photos queue offline.",
                13,
            ),
            SeedTopic(
                "Accessibility and next steps",
                "Contrast and 48px targets verified; large-font testing pending; prototype sessions with six drivers next week.",
                22,
            ),
        ],
        action_items=[
            SeedActionItem(
                "Prototype the collapsing route summary card", "Sarah", 12, completed=True
            ),
            SeedActionItem(
                "Write a technical note on the offline photo upload queue",
                "Noah",
                21,
                completed=True,
            ),
            SeedActionItem("Test all screens with the largest system font size", "Noah", 23, 4),
            SeedActionItem(
                "Add the report-issue button and long-press sheet to the prototype", "Sarah", 25, 2
            ),
            SeedActionItem("Schedule prototype sessions with the six drivers", "Sarah", 25, 3),
        ],
    ),
    SeedMeeting(
        title="Senior Backend Engineer — Hiring Debrief",
        days_ago=11,
        time=(11, 0),
        participants=["Aisha Patel", "Arjun Mehta", "David Kim"],
        lines=[
            (
                "Aisha",
                "Thanks for coming. We're debriefing on Ravi, the senior backend candidate who finished the onsite yesterday. Same format as always: each interviewer gives their signal and evidence first, then we discuss. David, you did system design.",
            ),
            (
                "David",
                "Strong hire from me. The prompt was designing a delivery-tracking service for a few million events a day. He started by asking about read versus write patterns before drawing anything, which I always look for.",
            ),
            (
                "David",
                "He chose an append-only event log with a separate read model for the tracking page and explained why. When I asked what happens if the consumer falls behind, he talked about lag monitoring and replaying from offsets without me prompting.",
            ),
            ("Arjun", "Any weaknesses?"),
            (
                "David",
                "His first data model was over-normalized for the read path, but when I pointed at the query he'd need, he fixed it himself. That's the kind of correction I'm happy to see.",
            ),
            ("Aisha", "Arjun, you did the coding round."),
            (
                "Arjun",
                "Hire, but not strong hire. He solved the problem, a rate limiter with a sliding window, and his code was clean and well named. But he didn't write a single test until I asked, and his first version had an off-by-one at the window boundary.",
            ),
            ("David", "Did he find the bug himself?"),
            (
                "Arjun",
                "Once he wrote the tests, yes, within a couple of minutes. So the instinct is there, it just wasn't his default under time pressure.",
            ),
            (
                "Aisha",
                "I did the values and collaboration interview. Strong hire. He described a migration at his last company where he disagreed with his tech lead, wrote down both options with their costs, and then fully committed when the decision went the other way.",
            ),
            (
                "Aisha",
                "He also mentioned mentoring two junior engineers and gave concrete examples, like pairing with them during their first on-call week.",
            ),
            (
                "Arjun",
                "That matters for us. If we hire him he'd likely mentor Noah on backend work.",
            ),
            (
                "Aisha",
                "On logistics: his notice period is six weeks, and his expectation is at the top of our band for this level.",
            ),
            (
                "Arjun",
                "Given the system design signal, I'm comfortable with the top of the band. I'd rather not lose him over a small difference.",
            ),
            ("David", "Agreed. Design ability at that level is hard to find."),
            (
                "Aisha",
                "Then the recommendation is hire, at senior level. Any concerns we should probe in reference checks?",
            ),
            (
                "Arjun",
                "Testing habits. I'd ask a former teammate how he approaches testing on real projects, not in interviews.",
            ),
            (
                "Aisha",
                "Good. I'll run two reference checks this week, one manager and one peer, and include that question.",
            ),
            (
                "Aisha",
                "If the references are positive, I'll prepare the offer at the top of the band, with a start date after his notice period, probably early December.",
            ),
            (
                "Arjun",
                "Can we also send him the architecture overview before he starts? It shortens onboarding a lot.",
            ),
            (
                "David",
                "I'll update that document first. Parts of it still describe the old monolith.",
            ),
            (
                "Aisha",
                "Thanks everyone. Decision recorded as hire. I'll share the reference results in the hiring channel by Friday.",
            ),
        ],
        overview=(
            "The panel recommended hiring Ravi as a senior backend engineer. System design was a strong "
            "hire: he clarified read/write patterns first, chose an event log with a separate read "
            "model, and raised consumer lag and replay unprompted. Coding was a hire: clean code, but "
            "tests only after prompting, which exposed an off-by-one he then fixed. Values were strong, "
            "with concrete examples of disagree-and-commit and mentoring. The offer will be at the top "
            "of the band, pending manager and peer references that probe testing habits; start is "
            "likely early December."
        ),
        keywords=[
            "Hiring debrief",
            "Senior backend",
            "System design",
            "Testing",
            "References",
            "Offer",
        ],
        topics=[
            SeedTopic(
                "System design interview",
                "Strong hire: event log plus read model, proactive discussion of consumer lag and replay.",
                0,
            ),
            SeedTopic(
                "Coding interview",
                "Hire: correct, clean sliding-window rate limiter, but tests only when asked.",
                5,
            ),
            SeedTopic(
                "Values and collaboration",
                "Strong hire: documented trade-offs, committed to the team decision, mentors juniors.",
                9,
            ),
            SeedTopic(
                "Compensation and decision",
                "Six-week notice, top of band accepted; recommendation is hire at senior level.",
                12,
            ),
            SeedTopic(
                "References and onboarding",
                "Two references focused on testing habits; architecture overview to be updated before he starts.",
                16,
            ),
        ],
        action_items=[
            SeedActionItem(
                "Run manager and peer reference checks, including testing habits",
                "Aisha",
                17,
                completed=True,
            ),
            SeedActionItem("Prepare the offer at the top of the band", "Aisha", 18, 2),
            SeedActionItem("Update the architecture overview document", "David", 20, 5),
            SeedActionItem(
                "Share reference results in the hiring channel", "Aisha", 21, completed=True
            ),
        ],
    ),
    SeedMeeting(
        title="Q4 Marketing Strategy",
        days_ago=16,
        time=(14, 0),
        participants=["Elena Rodriguez", "Marcus Johnson", "Priya Sharma", "Kenji Tanaka"],
        lines=[
            (
                "Elena",
                "Okay, let's go. This is Q4 planning for marketing. I want us to agree on three things: the main campaign theme, the budget split across channels, and how sales and marketing hand off leads. Kenji has the Q3 numbers.",
            ),
            (
                "Kenji",
                "Quick summary. We spent a hundred and twenty thousand in Q3 and generated four hundred and ten qualified leads. Cost per qualified lead was about two hundred and ninety dollars, down from three hundred and forty in Q2.",
            ),
            (
                "Kenji",
                "By channel, LinkedIn ads were the most expensive at around four hundred and fifty per lead, but those leads converted to pipeline at twice the rate of paid search.",
            ),
            (
                "Marcus",
                "That matches what my team sees. The LinkedIn leads are operations managers at mid-sized fleets, exactly who we want. Paid search brings a lot of very small companies.",
            ),
            (
                "Elena",
                "So for Q4 I'm proposing we shift budget away from paid search and toward LinkedIn and events. Roughly forty percent LinkedIn, twenty-five events, twenty content, and fifteen search.",
            ),
            (
                "Kenji",
                "If we keep the same total budget, that should lower our lead count but raise pipeline value. My model says about three hundred and forty leads, but roughly twenty percent more pipeline.",
            ),
            ("Priya", "I'm fine with fewer, better leads, as long as sales agrees."),
            ("Marcus", "We do. My reps are wasting time on companies with five trucks."),
            (
                "Elena",
                "Campaign theme. I want Q4 to be about planning hours saved. Every customer conversation mentions how long dispatchers spend building routes by hand.",
            ),
            (
                "Priya",
                "The Brightline call is a perfect example. Their dispatchers spend two hours every evening adjusting routes. If the pilot goes well, that becomes a case study.",
            ),
            (
                "Marcus",
                "I'd be careful about promising a case study before they sign. But we can use anonymized numbers from existing customers right away.",
            ),
            (
                "Elena",
                "Agreed. Kenji, can you pull planning-time data from our five largest customers, before and after onboarding?",
            ),
            ("Kenji", "Yes, we have it in the usage data. I'll have a summary by next Friday."),
            (
                "Elena",
                "Events. Two matter in Q4: the regional logistics expo in Chicago and a supply chain summit in Atlanta. A booth at Chicago, and a speaking slot in Atlanta if we can get one.",
            ),
            (
                "Marcus",
                "Chicago is where most of our Midwest pipeline comes from. I'll staff the booth with two reps and a solutions engineer.",
            ),
            (
                "Priya",
                "I can give the talk in Atlanta. Something practical, like what we learned optimizing routes with real-world constraints.",
            ),
            (
                "Elena",
                "Lead handoff is the last item. Right now marketing qualified leads sit in the CRM for an average of three days before a rep reaches out.",
            ),
            (
                "Marcus",
                "That's too slow, I know. My proposal: any lead from a company with more than fifty vehicles gets a call within one business day, and the rest go into a nurture sequence.",
            ),
            (
                "Kenji",
                "I can build a dashboard that tracks time to first contact by rep, so we can see whether we're hitting that.",
            ),
            (
                "Elena",
                "Great. And we'll add fleet size to the demo request form, so the routing is automatic.",
            ),
            (
                "Priya",
                "Let's make sure the form doesn't get long. Every extra field costs conversions.",
            ),
            (
                "Elena",
                "Just one field, a dropdown with ranges. I'll test it against the current form for two weeks.",
            ),
            (
                "Elena",
                "So to summarize: budget moves toward LinkedIn and events, the theme is planning hours saved, a Chicago booth and an Atlanta talk, and leads from larger fleets get a call within a day.",
            ),
            ("Marcus", "Sounds right. Let's review the numbers again in mid-November."),
        ],
        overview=(
            "Q3 produced 410 qualified leads at ~$290 each; LinkedIn leads cost more ($450) but "
            "converted to pipeline at twice the rate of paid search. Q4 budget shifts to 40% LinkedIn, "
            "25% events, 20% content and 15% search — Kenji projects ~340 leads but ~20% more "
            'pipeline. The campaign theme is "planning hours saved", backed by anonymized customer '
            "data (a Brightline case study only after they sign). Events: a booth at the Chicago "
            "logistics expo and a talk by Priya in Atlanta. Leads from fleets over 50 vehicles must be "
            "called within one business day, tracked on a new dashboard."
        ),
        keywords=["Q4 campaign", "Budget", "LinkedIn", "Events", "Lead handoff", "Case study"],
        topics=[
            SeedTopic(
                "Q3 results by channel",
                "410 qualified leads at ~$290; LinkedIn leads cost more but convert to pipeline at 2× paid search.",
                1,
            ),
            SeedTopic(
                "Q4 budget split",
                "40% LinkedIn, 25% events, 20% content, 15% search: fewer leads, ~20% more pipeline.",
                4,
            ),
            SeedTopic(
                "Campaign theme: planning hours saved",
                "Use anonymized before/after planning-time data; no Brightline case study until signed.",
                8,
            ),
            SeedTopic(
                "Events: Chicago and Atlanta",
                "Booth at the Chicago expo staffed by sales; Priya speaks in Atlanta.",
                13,
            ),
            SeedTopic(
                "Sales and marketing lead handoff",
                "Large-fleet leads called within one business day; fleet-size field A/B tested; dashboard for time to first contact.",
                16,
            ),
        ],
        action_items=[
            SeedActionItem(
                "Pull before/after planning-time data for the five largest customers",
                "Kenji",
                11,
                completed=True,
            ),
            SeedActionItem(
                "Staff the Chicago expo booth with two reps and a solutions engineer",
                "Marcus",
                14,
                completed=True,
            ),
            SeedActionItem("Submit the Atlanta summit talk proposal", "Priya", 15, -2),
            SeedActionItem("Build a time-to-first-contact dashboard by rep", "Kenji", 18, 6),
            SeedActionItem(
                "A/B test the fleet-size field on the demo request form", "Elena", 21, 7
            ),
        ],
    ),
    SeedMeeting(
        title="Q1 Planning Kickoff",
        days_ago=23,
        time=(9, 30),
        participants=[
            "Priya Sharma",
            "Arjun Mehta",
            "Elena Rodriguez",
            "Marcus Johnson",
            "Kenji Tanaka",
        ],
        lines=[
            (
                "Priya",
                "Good morning. This is the kickoff for Q1 planning. The goal today isn't to finalize the roadmap, it's to agree on the two or three outcomes we want by the end of March. Kenji, can you set the context?",
            ),
            (
                "Kenji",
                "Sure. We closed September at two point one million in annual recurring revenue, growing about six percent month over month. Net revenue retention is a hundred and twelve percent. Gross churn is low, but almost all of it comes from customers with fewer than twenty vehicles.",
            ),
            (
                "Marcus",
                "Which is consistent with the sales feedback. Small fleets churn, mid-sized fleets expand.",
            ),
            (
                "Priya",
                "So the first outcome I'd propose is to win more mid-sized fleets, between fifty and five hundred vehicles. That's where retention and expansion are strongest.",
            ),
            (
                "Arjun",
                "What does that mean for engineering? Mid-sized fleets need integrations more than small ones do.",
            ),
            (
                "Marcus",
                "Exactly. The top three blockers in lost deals last quarter were SSO, an API for order import, and integration with their telematics provider.",
            ),
            (
                "Arjun",
                "SSO and the order API we have, at least partly. Telematics is new work. We'd need to pick one or two providers to start.",
            ),
            (
                "Kenji",
                "Looking at the CRM, Samsara and Geotab cover about seventy percent of the prospects who mentioned telematics.",
            ),
            (
                "Arjun",
                "Then a Samsara integration is a reasonable Q1 goal, and Geotab in Q2 if the first one goes well. I'll need a spike to estimate it properly.",
            ),
            (
                "Elena",
                "The second outcome I'd like is around activation. The onboarding checklist helped a lot, but we still lose about half of all trials in the first week.",
            ),
            (
                "Priya",
                "Agreed. Let's make it measurable: seven-day activation from fifty-one percent to sixty-five percent by the end of Q1.",
            ),
            (
                "Elena",
                "That's ambitious, but the sample data idea and the import fix should get us a good part of the way.",
            ),
            (
                "Arjun",
                "The third thing I want on the list is reliability. The webhook incident showed we have gaps. I'd like an uptime target and an on-call rotation that isn't just me and David.",
            ),
            ("Priya", "What target are you thinking?"),
            (
                "Arjun",
                "Ninety-nine point nine percent for the API and the dispatcher app, measured monthly. And every customer-facing incident gets a postmortem within a week.",
            ),
            (
                "Marcus",
                "Enterprise prospects ask about this on every security questionnaire. A published target would help sales.",
            ),
            (
                "Priya",
                "Then reliability is the third outcome. Let's be careful about capacity, though. Three outcomes with the current team is already a lot.",
            ),
            (
                "Kenji",
                "On capacity, we're approved for two more engineering hires in Q1. If the senior backend offer goes out this month, he could start in December.",
            ),
            (
                "Arjun",
                "That helps, but new hires take a month or two to be fully productive. I'd plan Q1 assuming our current team and treat new hires as upside.",
            ),
            (
                "Priya",
                "Good principle. So, three outcomes: grow mid-sized fleets with SSO, the order API and a Samsara integration; raise activation to sixty-five percent; and reach ninety-nine point nine percent uptime with a real on-call rotation.",
            ),
            ("Elena", "Can each outcome have a single owner? Otherwise it gets blurry."),
            (
                "Priya",
                "Yes. I'll own activation, Arjun owns reliability, and Marcus and Arjun share mid-sized fleets: Marcus for the commercial side and Arjun for the integration.",
            ),
            (
                "Arjun",
                "I'll run the Samsara spike over the next two weeks so the estimate is real.",
            ),
            (
                "Priya",
                "Next step: each owner writes a one-page plan with milestones and metrics, and we review them together in two weeks. Kenji, can you set up the metric definitions so we all measure the same way?",
            ),
            (
                "Kenji",
                "Yes. I'll write the definitions for activation, uptime and the mid-market pipeline and share them before the review.",
            ),
            ("Priya", "Thanks everyone, this was a productive start."),
        ],
        overview=(
            "Q1 planning kickoff. Context: $2.1M ARR growing ~6% month over month, 112% net revenue "
            "retention, churn concentrated in fleets under 20 vehicles. Three outcomes were agreed: "
            "(1) win mid-sized fleets (50–500 vehicles) by closing the SSO, order API and telematics "
            "gaps, starting with Samsara; (2) raise 7-day activation from 51% to 65%; (3) reach 99.9% "
            "monthly uptime with a real on-call rotation and postmortems within a week. Plans assume "
            "the current team, with new hires as upside. Owners write one-page plans for review in "
            "two weeks."
        ),
        keywords=["Q1 planning", "Mid-market", "Telematics", "Activation", "Reliability", "OKRs"],
        topics=[
            SeedTopic(
                "Business context",
                "$2.1M ARR, 6% monthly growth, 112% NRR; churn comes from very small fleets.",
                1,
            ),
            SeedTopic(
                "Outcome 1: win mid-sized fleets",
                "Lost deals cite SSO, order import API and telematics; Samsara first, Geotab in Q2.",
                3,
            ),
            SeedTopic(
                "Outcome 2: raise activation",
                "Seven-day activation target from 51% to 65% by end of Q1.",
                9,
            ),
            SeedTopic(
                "Outcome 3: reliability and on-call",
                "99.9% monthly uptime for API and dispatcher app, postmortems within a week.",
                12,
            ),
            SeedTopic(
                "Capacity, ownership and next steps",
                "Plan with the current team; single owners per outcome; one-page plans in two weeks.",
                17,
            ),
        ],
        action_items=[
            SeedActionItem("Run a two-week Samsara integration spike", "Arjun", 22, completed=True),
            SeedActionItem(
                "Write the one-page plan for the activation outcome", "Priya", 23, completed=True
            ),
            SeedActionItem(
                "Write the one-page plan for the reliability outcome", "Arjun", 23, completed=True
            ),
            SeedActionItem("Set up an on-call rotation beyond Arjun and David", "Arjun", 12, 5),
            SeedActionItem(
                "Write metric definitions for activation, uptime and mid-market pipeline",
                "Kenji",
                24,
                completed=True,
            ),
        ],
    ),
]

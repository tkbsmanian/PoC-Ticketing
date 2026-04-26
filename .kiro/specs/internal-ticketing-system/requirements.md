# Requirements Document

## Product Brief

### Goals

- Provide business users with a self-service portal to submit, track, and manage service and business requests
- Automatically create and synchronize pending tasks in JIRA when a request is submitted, ensuring IT teams work from a single task management system
- Give IT users a structured workflow to review, categorize, prioritize, and update request lifecycle within the portal
- Deliver a working PoC that validates the end-to-end flow from request submission to JIRA task creation and status tracking

### Non-Goals

- This PoC does not replace or fully integrate with existing ITSM platforms (e.g., ServiceNow)
- This PoC does not support external (non-employee) users
- Advanced reporting, SLA enforcement, or automated routing rules are out of scope for the PoC
- Mobile-native applications are out of scope; the portal is web-only
- Single Sign-On (SSO) or Active Directory integration is out of scope for the PoC (basic auth is acceptable)
- Automated resolution or AI-assisted triage is out of scope

### Personas

- **Business User**: An internal employee who submits service or business requests, tracks their status, and communicates via comments. Has no IT administrative privileges.
- **IT User**: An internal IT team member who reviews incoming requests, categorizes and prioritizes them, updates lifecycle status, and resolves tickets. Has elevated portal privileges.
- **Portal Admin**: An IT administrator responsible for configuring the portal (categories, user roles). May overlap with the IT User persona for the PoC.

### Assumptions

- The organization has an active JIRA instance accessible via the JIRA REST API with valid credentials
- All users (business and IT) have accounts provisioned in the portal
- Network connectivity between the portal server and the JIRA instance is available and reliable
- JIRA project keys and issue types are pre-configured before the PoC is deployed
- The PoC will be hosted locally (localhost) and is not intended for production-scale load

### Constraints

- The system must be locally hosted (no cloud deployment required for the PoC)
- JIRA integration must use the JIRA REST API v3
- The portal must be a web application accessible via a standard browser
- All data must be persisted in a local database (e.g., SQLite or PostgreSQL)
- The PoC must support a minimum of two user roles: Business User and IT User

### Success Criteria

- A business user can submit a request through the portal and receive a confirmation with a ticket ID
- Within 30 seconds of submission, a corresponding JIRA task is created in the configured project with status "Pending"
- A business user can view the current status, full comment history, and lifecycle history of their submitted requests
- An IT user can update the status, category, priority, and add comments to any request
- Status changes made in the portal are reflected in the corresponding JIRA task within 60 seconds
- The end-to-end flow (submit → JIRA sync → status update → visible to business user) is demonstrable in a single session

---

## Introduction

The Internal Ticketing System is a locally hosted web portal that enables business users to submit service and business requests, track their progress, and communicate with IT. Every request submitted through the portal automatically creates a corresponding task in JIRA, ensuring IT teams can manage work from their existing tooling. IT users can review, categorize, prioritize, and update requests through the portal, with changes synchronized back to JIRA.

---

## Glossary

- **Portal**: The web application through which business users and IT users interact with the ticketing system
- **Request**: A service or business request submitted by a Business User through the Portal
- **Ticket**: The Portal's internal representation of a Request, identified by a unique Ticket_ID
- **JIRA_Task**: The corresponding issue created in JIRA when a Ticket is submitted
- **Business_User**: An internal employee with permission to submit and track Requests
- **IT_User**: An internal IT team member with permission to review, update, and resolve Tickets
- **Portal_Admin**: A user with administrative privileges to configure Portal settings
- **JIRA_Sync_Service**: The background service responsible for creating and updating JIRA_Tasks in response to Ticket events
- **Lifecycle_Status**: The current state of a Ticket (e.g., Pending, In Review, In Progress, Resolved, Closed)
- **Category**: A classification label applied to a Ticket by an IT_User (e.g., Hardware, Software, Access, General)
- **Priority**: An urgency level assigned to a Ticket by an IT_User (e.g., Low, Medium, High, Critical)
- **Comment**: A text message attached to a Ticket by either a Business_User or IT_User
- **Ticket_History**: An ordered log of all Lifecycle_Status changes and significant events on a Ticket
- **SLA**: A Service Level Agreement defining target response and resolution times for Tickets by Priority
- **Notification**: An email or in-app alert sent to a user in response to a Ticket event

---

## Scope Legend

- **[PoC]** — Required for the Proof of Concept. Must be implemented to validate the end-to-end flow.
- **[Production]** — Required for a production-ready system. Not in scope for the PoC.
- **[Future]** — Explicitly out of scope for both PoC and initial production. Captured for roadmap planning.

---

## 1. Functional Requirements

### FR-1: Request Submission

**User Story:** As a Business_User, I want to submit a service or business request through the Portal, so that IT can review and action my request.

#### Acceptance Criteria

1. **[PoC]** THE Portal SHALL provide a request submission form containing at minimum: a title field, a description field, and a category selection field.
2. **[PoC]** WHEN a Business_User submits a valid request form, THE Portal SHALL create a Ticket with a unique Ticket_ID and set its Lifecycle_Status to "Pending".
3. **[PoC]** WHEN a Business_User submits a valid request form, THE Portal SHALL display a confirmation message containing the assigned Ticket_ID.
4. **[PoC]** IF a Business_User submits a request form with a missing title or missing description, THEN THE Portal SHALL display a validation error message and SHALL NOT create a Ticket.
5. **[Production]** WHEN a Business_User submits a valid request form, THE Portal SHALL send a confirmation Notification to the Business_User's registered email address containing the Ticket_ID and a link to the Ticket detail view.
6. **[Production]** THE Portal SHALL allow a Business_User to attach files up to 10 MB per attachment to a Request at submission time.

---

### FR-2: Request Visibility and Tracking

**User Story:** As a Business_User, I want to view the status, comments, and history of my submitted requests, so that I can track progress without contacting IT directly.

#### Acceptance Criteria

1. **[PoC]** WHEN a Business_User accesses the Portal, THE Portal SHALL display a list of all Tickets submitted by that Business_User.
2. **[PoC]** WHEN a Business_User selects a Ticket, THE Portal SHALL display the Ticket's current Lifecycle_Status, Category, Priority, full Comment thread, and Ticket_History.
3. **[PoC]** WHILE a Ticket's Lifecycle_Status is not "Closed", THE Portal SHALL allow the Business_User to add a Comment to the Ticket.
4. **[PoC]** WHEN a Comment is added by a Business_User, THE Portal SHALL record the Comment with the author's identity and a timestamp.
5. **[PoC]** THE Portal SHALL display Ticket_History entries in chronological order, showing the previous Lifecycle_Status, the new Lifecycle_Status, the actor, and the timestamp of each change.
6. **[Production]** WHEN the Lifecycle_Status of a Ticket submitted by a Business_User changes, THE Portal SHALL send a Notification to that Business_User containing the new Lifecycle_Status and the Ticket_ID.

---

### FR-3: IT User Request Management

**User Story:** As an IT_User, I want to review, categorize, prioritize, and update the lifecycle of submitted requests, so that I can manage and resolve business needs efficiently.

#### Acceptance Criteria

1. **[PoC]** WHEN an IT_User accesses the Portal, THE Portal SHALL display a list of all Tickets across all Business_Users, filterable by Lifecycle_Status, Category, and Priority.
2. **[PoC]** WHEN an IT_User selects a Ticket, THE Portal SHALL allow the IT_User to update the Lifecycle_Status to any valid state in the lifecycle (Pending → In Review → In Progress → Resolved → Closed).
3. **[PoC]** WHEN an IT_User updates the Lifecycle_Status of a Ticket, THE Portal SHALL record the change in the Ticket_History with the IT_User's identity and a timestamp.
4. **[PoC]** WHEN an IT_User selects a Ticket, THE Portal SHALL allow the IT_User to assign or update the Category and Priority of the Ticket.
5. **[PoC]** WHEN an IT_User adds a Comment to a Ticket, THE Portal SHALL record the Comment with the IT_User's identity and a timestamp.
6. **[Production]** THE Portal SHALL allow an IT_User to reassign a Ticket to a specific IT_User, recording the reassignment in the Ticket_History with the actor's identity and a timestamp.
7. **[Production]** THE Portal SHALL allow an IT_User to bulk-update the Lifecycle_Status or Priority of up to 50 selected Tickets in a single operation.

---

### FR-4: User Authentication and Role Enforcement

**User Story:** As a Portal_Admin, I want users to authenticate before accessing the Portal and have their permissions enforced by role, so that Tickets and data are only accessible to authorized users.

#### Acceptance Criteria

1. **[PoC]** WHEN an unauthenticated user attempts to access any Portal page, THE Portal SHALL redirect the user to the login page.
2. **[PoC]** WHEN a user provides valid credentials, THE Portal SHALL authenticate the user and establish a session.
3. **[PoC]** IF a user provides invalid credentials, THEN THE Portal SHALL display an authentication error message and SHALL NOT establish a session.
4. **[PoC]** WHILE a Business_User is authenticated, THE Portal SHALL restrict the Business_User to viewing and interacting only with Tickets submitted by that Business_User.
5. **[PoC]** WHILE an IT_User is authenticated, THE Portal SHALL grant the IT_User access to all Tickets and IT management actions.
6. **[PoC]** WHEN an authenticated session exceeds 8 hours of inactivity, THE Portal SHALL invalidate the session and require the user to re-authenticate.
7. **[Production]** WHERE SSO is configured, THE Portal SHALL authenticate users via the organization's identity provider using the SAML 2.0 protocol instead of local credentials.
8. **[Production]** THE Portal SHALL enforce multi-factor authentication for all IT_User and Portal_Admin accounts.

---

### FR-5: Data Persistence

**User Story:** As a Business_User, I want my submitted requests and their history to be reliably stored, so that data is not lost between sessions or server restarts.

#### Acceptance Criteria

1. **[PoC]** THE Portal SHALL persist all Tickets, Comments, Ticket_History entries, and user records in a local database.
2. **[PoC]** WHEN the Portal server is restarted, THE Portal SHALL restore all previously persisted Tickets, Comments, and Ticket_History entries without data loss.
3. **[PoC]** THE Portal SHALL store each Ticket with at minimum: Ticket_ID, title, description, Category, Priority, Lifecycle_Status, submitting Business_User identity, creation timestamp, and last updated timestamp.
4. **[Production]** THE Portal SHALL perform automated daily backups of the database and retain backups for a minimum of 30 days.
5. **[Production]** WHEN a database backup is completed, THE Portal SHALL verify the backup integrity and log the result with a timestamp.

---

## 2. Non-Functional Requirements

### NFR-1: Performance

**User Story:** As a Business_User or IT_User, I want the Portal to respond promptly to my actions, so that I can work efficiently without waiting for slow page loads.

#### Acceptance Criteria

1. **[PoC]** WHEN a user submits a request form, THE Portal SHALL display the confirmation message within 3 seconds under local single-user load.
2. **[PoC]** WHEN a user navigates to the Ticket list view, THE Portal SHALL render the page within 3 seconds under local single-user load.
3. **[Production]** WHEN any Portal page is requested by an authenticated user, THE Portal SHALL return a fully rendered response within 2 seconds at the 95th percentile under a concurrent load of 100 users.
4. **[Production]** THE Portal SHALL support a minimum of 500 concurrent authenticated sessions without degradation of response times beyond the defined thresholds.

---

### NFR-2: Reliability

**User Story:** As a Business_User, I want the Portal to be available when I need to submit or track requests, so that I am not blocked from raising issues with IT.

#### Acceptance Criteria

1. **[PoC]** WHEN the JIRA_Sync_Service fails to create or update a JIRA_Task, THE Portal SHALL continue to accept and display Tickets without interruption.
2. **[Production]** THE Portal SHALL maintain a minimum uptime of 99.5% measured over any rolling 30-day period, excluding scheduled maintenance windows.
3. **[Production]** WHEN a scheduled maintenance window is planned, THE Portal SHALL display a maintenance notice to all authenticated users at least 24 hours in advance.

---

### NFR-3: Security

**User Story:** As a Portal_Admin, I want the Portal to protect user data and prevent unauthorized access, so that sensitive request information is not exposed.

#### Acceptance Criteria

1. **[PoC]** THE Portal SHALL store all user passwords as salted cryptographic hashes using bcrypt with a minimum cost factor of 12.
2. **[PoC]** THE Portal SHALL transmit all data between the browser and the server over HTTPS.
3. **[Production]** THE Portal SHALL enforce a Content Security Policy header on all responses to mitigate cross-site scripting attacks.
4. **[Production]** THE Portal SHALL log all authentication events (successful login, failed login, session expiry) with the user identity, timestamp, and source IP address.
5. **[Production]** THE Portal SHALL undergo a third-party penetration test before go-live and SHALL remediate all critical and high findings before launch.

---

### NFR-4: Usability

**User Story:** As a Business_User, I want the Portal interface to be intuitive, so that I can submit and track requests without requiring training.

#### Acceptance Criteria

1. **[PoC]** THE Portal SHALL display inline validation error messages adjacent to the relevant form field when a submission fails validation.
2. **[Production]** THE Portal SHALL conform to WCAG 2.1 Level AA accessibility guidelines for all user-facing pages.
3. **[Production]** THE Portal SHALL render correctly on the latest two major versions of Chrome, Firefox, Edge, and Safari.

---

## 3. Integration Requirements

### IR-1: JIRA Task Creation

**User Story:** As an IT_User, I want every Portal Ticket to have a corresponding JIRA task created automatically, so that I can manage work from my existing JIRA workflow without manual duplication.

#### Acceptance Criteria

1. **[PoC]** WHEN a Ticket is created in the Portal, THE JIRA_Sync_Service SHALL create a JIRA_Task in the configured JIRA project within 30 seconds, populating the JIRA_Task with the Ticket title, description, and initial Lifecycle_Status mapped to the corresponding JIRA issue status.
2. **[PoC]** WHEN the JIRA_Task is created, THE JIRA_Sync_Service SHALL store the JIRA_Task identifier on the Ticket record.
3. **[PoC]** THE JIRA_Sync_Service SHALL use the JIRA REST API v3 for all JIRA_Task operations.
4. **[PoC]** THE Portal SHALL display the JIRA_Task identifier as a reference link on the Ticket detail view WHERE a JIRA_Task has been successfully created.
5. **[Production]** WHEN a Business_User attaches a file to a Ticket, THE JIRA_Sync_Service SHALL attach the same file to the corresponding JIRA_Task within 60 seconds.

---

### IR-2: JIRA Status and Comment Synchronization

**User Story:** As an IT_User, I want Ticket status changes and comments in the Portal to be reflected in JIRA, so that JIRA remains the authoritative source of work state for IT teams.

#### Acceptance Criteria

1. **[PoC]** WHEN the Lifecycle_Status of a Ticket is updated in the Portal, THE JIRA_Sync_Service SHALL update the status of the corresponding JIRA_Task to the mapped JIRA status within 60 seconds.
2. **[PoC]** WHEN a Comment is added to a Ticket in the Portal, THE JIRA_Sync_Service SHALL add the Comment text and author to the corresponding JIRA_Task within 60 seconds.
3. **[PoC]** IF the JIRA REST API returns an error response, THEN THE JIRA_Sync_Service SHALL log the error with the Ticket_ID, the attempted operation, and the error response details.
4. **[PoC]** IF a JIRA_Task update fails, THEN THE JIRA_Sync_Service SHALL retry the update at least once before marking the sync as failed.
5. **[Production]** WHEN a JIRA_Task status is updated directly in JIRA outside the Portal, THE JIRA_Sync_Service SHALL detect the change within 5 minutes and update the corresponding Ticket's Lifecycle_Status in the Portal.
6. **[Production]** THE JIRA_Sync_Service SHALL expose a health-check endpoint that returns the timestamp of the last successful sync operation and the count of pending sync retries.

---

## 4. Reporting Requirements

### RR-1: IT User Operational Dashboard

**User Story:** As an IT_User, I want a summary view of open Tickets by status and category, so that I can quickly assess the current workload and prioritize my work.

#### Acceptance Criteria

1. **[PoC]** WHEN an IT_User accesses the Portal, THE Portal SHALL display a count of Tickets grouped by Lifecycle_Status (Pending, In Review, In Progress, Resolved, Closed).
2. **[Production]** THE Portal SHALL provide an IT_User dashboard displaying: total open Tickets, Tickets by Category, Tickets by Priority, and average time in current Lifecycle_Status.
3. **[Production]** WHEN an IT_User applies a date range filter on the dashboard, THE Portal SHALL recalculate all displayed metrics to reflect only Tickets created within the selected date range.

---

### RR-2: Business User Request Summary

**User Story:** As a Business_User, I want to see a summary of my submitted requests by status, so that I can quickly understand the state of my outstanding requests.

#### Acceptance Criteria

1. **[PoC]** WHEN a Business_User accesses the Portal, THE Portal SHALL display the total count of that Business_User's Tickets grouped by Lifecycle_Status.
2. **[Production]** THE Portal SHALL allow a Business_User to filter their Ticket list by Lifecycle_Status, Category, and date range.
3. **[Production]** THE Portal SHALL allow a Business_User to export their Ticket list as a CSV file containing Ticket_ID, title, Category, Priority, Lifecycle_Status, creation timestamp, and last updated timestamp.

---

### RR-3: IT Management Reporting

**User Story:** As a Portal_Admin, I want exportable reports on Ticket volume and resolution metrics, so that I can report on IT team performance and identify bottlenecks.

#### Acceptance Criteria

1. **[Production]** THE Portal SHALL allow a Portal_Admin to generate a report of all Tickets within a specified date range, exportable as a CSV file.
2. **[Production]** THE Portal SHALL calculate and display the average time from Ticket creation to Lifecycle_Status "Resolved" for a specified date range, grouped by Category and Priority.
3. **[Production]** WHEN a Portal_Admin requests a report containing more than 10,000 Ticket records, THE Portal SHALL generate the report asynchronously and notify the Portal_Admin via email when the export is ready for download.

---

## 5. Audit Requirements

### AR-1: Ticket Lifecycle Audit Trail

**User Story:** As a Portal_Admin, I want every change to a Ticket to be recorded with actor identity and timestamp, so that I can audit the full history of any request.

#### Acceptance Criteria

1. **[PoC]** WHEN any Lifecycle_Status change occurs on a Ticket, THE Portal SHALL record an entry in the Ticket_History containing: the previous Lifecycle_Status, the new Lifecycle_Status, the identity of the actor, and the UTC timestamp of the change.
2. **[PoC]** WHEN a Category or Priority is assigned or changed on a Ticket, THE Portal SHALL record an entry in the Ticket_History containing: the field changed, the previous value, the new value, the identity of the actor, and the UTC timestamp.
3. **[PoC]** THE Portal SHALL retain Ticket_History entries for the full lifetime of the Ticket and SHALL NOT allow Ticket_History entries to be deleted or modified by any user role.
4. **[Production]** THE Portal SHALL retain all Ticket_History entries for a minimum of 3 years from the date of the Ticket's creation.
5. **[Production]** THE Portal SHALL allow a Portal_Admin to export the full Ticket_History for a specified Ticket as a CSV file.

---

### AR-2: Authentication and Access Audit Log

**User Story:** As a Portal_Admin, I want all authentication and access events to be logged, so that I can investigate unauthorized access attempts.

#### Acceptance Criteria

1. **[Production]** THE Portal SHALL log every successful login event with: user identity, timestamp, and source IP address.
2. **[Production]** THE Portal SHALL log every failed login attempt with: attempted username, timestamp, and source IP address.
3. **[Production]** THE Portal SHALL log every session expiry event with: user identity and timestamp.
4. **[Production]** THE Portal SHALL retain authentication audit logs for a minimum of 1 year.
5. **[Production]** WHEN more than 5 consecutive failed login attempts are recorded for a single user identity within a 10-minute window, THE Portal SHALL lock the account and notify the Portal_Admin via email.

---

### AR-3: JIRA Sync Audit Log

**User Story:** As a Portal_Admin, I want all JIRA synchronization operations to be logged, so that I can diagnose sync failures and verify data consistency between the Portal and JIRA.

#### Acceptance Criteria

1. **[PoC]** WHEN the JIRA_Sync_Service performs any JIRA_Task operation, THE JIRA_Sync_Service SHALL log the operation type, the Ticket_ID, the JIRA_Task identifier, the outcome (success or failure), and the UTC timestamp.
2. **[PoC]** WHEN a sync operation fails after all retries are exhausted, THE JIRA_Sync_Service SHALL mark the Ticket with a sync failure indicator visible to IT_Users in the Portal.
3. **[Production]** THE Portal SHALL allow a Portal_Admin to view a filterable log of all JIRA sync operations, filterable by outcome (success, failure) and date range.
4. **[Production]** THE Portal SHALL retain JIRA sync audit logs for a minimum of 1 year.

---

## 6. Future-Phase Requirements

> The following requirements are explicitly out of scope for both the PoC and the initial production release. They are captured here for roadmap planning purposes only.

### FFR-1: SSO and Active Directory Integration

**User Story:** As a Portal_Admin, I want users to authenticate using the organization's existing Active Directory credentials, so that user provisioning is centralized and employees do not need separate Portal passwords.

#### Notes

- Requires SAML 2.0 or OAuth 2.0 / OIDC integration with the organization's identity provider
- Dependent on IT infrastructure team providing IdP metadata and credentials
- Supersedes FR-4 credential-based authentication once implemented

---

### FFR-2: SLA Enforcement and Escalation

**User Story:** As a Portal_Admin, I want the Portal to automatically escalate overdue Tickets based on Priority-defined SLA thresholds, so that high-priority requests are not missed.

#### Notes

- Requires definition of SLA targets per Priority level (e.g., Critical: 4-hour response, High: 8-hour response)
- Escalation actions may include: Notification to IT_User, Notification to IT manager, automatic Priority upgrade
- Depends on Notification infrastructure (RR-3 and AR-2 email capabilities)

---

### FFR-3: Automated Routing Rules

**User Story:** As a Portal_Admin, I want incoming Tickets to be automatically assigned to the appropriate IT_User or team based on Category and keywords, so that manual triage time is reduced.

#### Notes

- Requires a rules engine or configuration interface for Portal_Admin to define routing logic
- May integrate with JIRA project routing or component assignments

---

### FFR-4: ServiceNow Integration

**User Story:** As a Portal_Admin, I want the Portal to optionally synchronize Tickets with ServiceNow in addition to JIRA, so that organizations using ServiceNow as their ITSM platform can adopt the Portal without replacing their existing tooling.

#### Notes

- Requires a pluggable sync adapter pattern in the JIRA_Sync_Service architecture
- ServiceNow REST API credentials and instance URL must be configurable per deployment

---

### FFR-5: Mobile-Native Application

**User Story:** As a Business_User, I want a native mobile application for iOS and Android, so that I can submit and track requests from my mobile device without using a browser.

#### Notes

- Out of scope for all web-based phases; requires a separate mobile development workstream
- Portal REST API must be designed with mobile client consumption in mind for future compatibility

---

### FFR-6: AI-Assisted Triage and Auto-Resolution

**User Story:** As an IT_User, I want the Portal to suggest Category, Priority, and potential resolutions for incoming Tickets based on historical data, so that triage time is reduced and common issues are resolved faster.

#### Notes

- Requires a sufficient volume of historical Ticket data to train or fine-tune a model
- May leverage an LLM API (e.g., Bedrock, OpenAI) for suggestion generation
- Auto-resolution actions must require IT_User confirmation before being applied

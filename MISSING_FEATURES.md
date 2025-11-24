# Missing Features and Issues

## Missing Admin Dashboard UI
The admin dashboard view exists in the backend (`admin_dashboard` function in `frontend_views.py`) but there's no template file for it. Administrators need a visual interface to see system statistics like total users, students, professors, consultations, and pending requests in one place without using the API directly.

## No Notification Center UI
While notification models and backend tasks are implemented, there's no frontend interface for users to view their in-app notifications. Users should have a notification bell icon in the navbar that shows unread notifications and a full notification center page where they can see all their consultation-related messages and mark them as read.

## Missing Consultation Search and Filter
The consultation list page doesn't have visible search or filter functionality on the frontend. Students and professors need to easily search consultations by title, filter by date range, or filter by status (pending, confirmed, cancelled) without manually scrolling through all consultations.

## Incomplete Test Coverage
There are only basic unit tests for models and a few API endpoints. The project needs more comprehensive tests for edge cases, validation logic, email notifications, Google Calendar integration failures, and frontend form submissions to ensure everything works correctly before deployment.

## Missing Professor Rating Display
Students can rate professors after consultations, but there's no aggregated rating display on the professor's profile or list page. Students should see average ratings and number of reviews when choosing a professor to help them make informed decisions about who to book.

## No Real-time Availability Checker
When students try to book a consultation, there's no real-time validation showing if the professor is already booked at that time. The system should check existing bookings and the professor's availability schedule before allowing submission to prevent double-booking conflicts.

## Celery Worker Not Configured
While Celery is configured in settings, there's no `celery.py` file in the main project directory to initialize the Celery app. Without this, background tasks like sending emails and syncing Google Calendar won't work, and the periodic reminder system won't run.

## Missing Email Configuration
The settings file references email configuration but doesn't have actual SMTP settings or environment variables defined. Email notifications won't work until proper email backend configuration is added with credentials for a service like Gmail SMTP, SendGrid, or AWS SES.

## No Cancel/Reschedule Time Limit
Students can cancel or reschedule consultations at any time, even minutes before the scheduled time. There should be a policy like "must cancel at least 4 hours in advance" to prevent last-minute cancellations that waste professors' time.

## Incomplete Error Handling
Many frontend views and API endpoints don't have proper try-catch blocks or validation for edge cases. If Google Calendar API fails, database constraints are violated, or invalid data is submitted, users might see generic error pages instead of helpful messages guiding them on what went wrong.

## Weak Mobile Responsiveness
Some parts of the frontend (consultation list, profile page, calendar view) don’t render well on mobile screens. Considering many students open the platform on their phones, responsive layouts are essential for smooth interaction, especially for quick actions like checking availability or viewing notifications.

## Missing pages after booking consultation
On the 'My Consultations' tab, the buttons to view, reschedule, cancel booking, add to calendar is not implemented.

## Using SQLite Instead of a Production-Ready Database
The project is still running on SQLite3, which is only suitable for local development and light testing. For deployment, this becomes a major limitation because SQLite cannot handle concurrent users, high-volume writes, or background tasks from Celery without risking slow performance or data integrity issues. The system should be upgraded to a production-grade database such as PostgreSQL or MySQL to ensure stable performance, proper transaction handling, and reliable scaling as more students and professors begin using the platform.

## Get the name from the google account used for addressing the user
Currently, for greeeting the user for example, the page uses the email instead of the name of the user.

## Better UI elements
(Optional) Implement what you think would make for a better user interface, consider the mobile experience as welll.
ex. have the tabs be in a burger button, a side bar
ex. implement darkmode

## Implement our name
Currently the site is named Prof Consult, change it to Consult Ease with our logo. Also, change the theme to match the colors of the logo.


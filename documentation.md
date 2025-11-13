# Professor Consultation Scheduler - Project Documentation

## Project Overview

### Purpose
A Django REST Framework-based web application that simplifies the process of scheduling and managing consultation sessions between professors and students.

### Core Features
- **User Management**: Separate authentication and roles for professors and students
- **Consultation Scheduling**: Professors can create and manage available time slots
- **Booking System**: Students can book available consultation slots
- **Google Calendar Integration**: Sync consultations with Google Calendar
- **Email Notifications**: Automated reminders and confirmations
- **Dashboard Analytics**: Track consultation statistics and status


### App Structure (Modular Design)

#### 1. **accounts** - User Management
- Custom User model with professor/student roles
- User profiles with additional information
- Authentication endpoints (register, login, logout)
- Token-based authentication

#### 2. **consultations** - Core Business Logic
- Consultation slot management
- Booking system
- Consultation notes and ratings
- Google Calendar integration
- Status tracking (pending, confirmed, completed, cancelled)

#### 3. **notifications** - Communication Layer
- Email notification system
- Celery tasks for async email sending
- Scheduled reminders (24 hours before consultation)
- Templates for different email types

___
## Model Details

#### User Model
- **Type**: Custom Django User (extends AbstractUser)
- **Fields**: username, email, password, user_type, first_name, last_name, phone_number
- **User Types**: 'professor' or 'student'
- **Relationships**: 1:1 with Profile, 1:N with ConsultationSlot (as professor), 1:N with Booking (as student)

#### Profile Model
- **Purpose**: Extended user information
- **Fields**: department, bio, profile_picture, google_calendar_token
- **Storage**: google_calendar_token stores OAuth2 credentials as JSON

#### ConsultationSlot Model
- **Purpose**: Time slots created by professors
- **Status Options**: available, booked, completed, cancelled
- **Validation**: end_time > start_time, no past slots
- **Indexes**: (professor, start_time), (status, start_time)

#### Booking Model
- **Purpose**: Student bookings for consultation slots
- **Status Options**: pending, confirmed, cancelled, completed, no_show
- **Constraints**: unique_together (slot, student) - one booking per student per slot
- **Validation**: Check slot availability and capacity

#### ConsultationNote Model
- **Purpose**: Post-consultation notes and ratings
- **Fields**: professor_notes, student_feedback, rating (1-5)
- **Relationship**: 1:1 with Booking
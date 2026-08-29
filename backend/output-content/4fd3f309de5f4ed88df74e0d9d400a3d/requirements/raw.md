# Requirements Analysis for NetworkPro (CareerPro-v2)

## Overview
NetworkPro is a career and networking application that analyzes LinkedIn profile data to provide personalized AI‑powered recommendations for career growth, networking, and skill development.

## Functional Requirements

### Profile Management
- The system must allow users to upload LinkedIn profile PDF files for analysis  
- The system must extract professional data from uploaded PDFs including: name, headline, location, industry, experience, education, skills, and certifications  
- The system must store user profiles with all extracted professional data  
- The system must allow users to manually edit their profile data  
- The system must retrieve and display user profile information  

### Recommendation System
- The system must generate networking recommendations including:  
  - People to follow based on profile analysis  
  - People to connect with based on profile analysis  
  - Trending posts relevant to user's professional interests  
- The system must generate job recommendations including:  
  - Job openings matching user profile and goals  
  - Recommended courses for skill development  
  - Skills to develop based on career goals and market trends  
- The system must refresh recommendations when user interests or career goals are updated  

### Interest and Goal Management
- The system must allow users to select career interest topics from suggested lists  
- The system must allow users to add custom career interest topics  
- The system must allow users to select skills they want to develop or showcase  
- The system must allow users to set career goals including desired role, industry, location, and salary range  
- The system must save and retrieve user interests and career goals  

### Bookmarking Functionality
- The system must allow users to save/bookmark items of various types (people, jobs, courses, posts, skills)  
- The system must allow users to remove saved items  
- The system must retrieve and display saved items by type  
- The system must persist saved items across user sessions  

### User Interface
- The system must provide tabbed navigation between four main sections: Home, Interests, Networking, and Jobs  
- The system must support light and dark mode themes with user preference persistence  
- The system must display loading states during asynchronous operations  
- The system must provide user feedback through toast notifications for success and error conditions  
- The system must handle empty states with appropriate placeholder content and guidance  

## Non-Functional Requirements

### Performance and Scalability
- The system must process file uploads up to 5 MB in size  
- The system must cache API responses to minimize unnecessary network requests  
- The system must provide responsive design that adapts to different screen sizes  

### Technical Architecture
- The system must use React 18+ for the frontend user interface  
- The system must use Express.js/Node.js for the backend API server  
- The system must use PostgreSQL as the primary database  
- The system must use TypeScript for type safety across frontend and backend  
- The system must use Drizzle ORM for database interactions  
- The system must use React Query for data fetching and state management  
- The system must use shadcn/ui component library with Radix UI primitives  

### Reliability and Error Handling
- The system must handle file upload errors gracefully (invalid file types, oversized files)  
- The system must handle API errors with user‑friendly error messages  
- The system must prevent stack traces from being exposed to end users  
- The system must maintain data consistency between client and server states  

### Security
- The system must authenticate users via username/password credentials  
- The system must manage user sessions securely  
- The system must validate file uploads for type (PDF only) and size limits  
- The system must use environment variables for sensitive configuration  
- The system must transmit credentials with API requests  

## Business and Domain Rules

### Data Validation
- Only PDF files are accepted for LinkedIn profile uploads  
- Uploaded files must not exceed 5 MB in size  
- User data must be associated with a valid user ID  
- Profile data must include a name field for processing  

### Workflow Dependencies
- Interest recommendations are generated based on analyzed profile data  
- Networking and job recommendations are generated based on profile and selected interests  
- Career goals influence the type of job and skill recommendations provided  
- Saved items persist until explicitly removed by the user  
- Theme preferences persist via browser localStorage  

### Data Processing
- Profile analysis extracts structured data from unstructured PDF text  
- Missing or incomplete profile data is supplemented with demo data for usability  
- Recommendation data is simulated/mocked for demonstration purposes  
- All dates and timestamps are stored in UTC format  

## Interface Requirements

### API Endpoints
- `POST /api/profile/upload` – Accepts multipart/form-data with PDF file, returns extracted profile data  
- `GET /api/profile` – Returns current user's profile data  
- `PUT /api/profile` – Accepts partial profile updates, returns updated profile  
- `GET /api/interests/suggestions` – Returns interest topic and skill suggestions based on profile  
- `POST /api/interests` – Accepts topics and skills arrays, saves user interests  
- `GET /api/interests` – Returns current user's saved interests  
- `GET /api/recommendations/networking` – Returns networking recommendations (people to follow, connect with, trending posts)  
- `GET /api/recommendations/jobs` – Returns job recommendations (openings, courses, skills to develop)  
- `POST /api/career-goals` – Accepts career goals object, saves or updates user goals  
- `GET /api/career-goals` – Returns current user's career goals  
- `POST /api/saved-items` – Accepts item to save, returns saved item with ID  
- `DELETE /api/saved-items/:id` – Removes saved item by ID, returns success status  
- `GET /api/saved-items` – Returns user's saved items, optionally filtered by type  

### Data Formats
- All API communication uses JSON format  
- File uploads use multipart/form-data encoding  
- Dates are transmitted as ISO 8601 strings  
- Enums and fixed values are represented as strings  
- Arrays are used for lists of items (experience, education, skills, etc.)  

## Data Requirements

### User Profile Entity
- **Required fields:** `userId`, `name`  
- **Optional fields:** `headline`, `location`, `industry`, `currentJobTitle`, `currentCompany`, `summary`, `avatarUrl`  
- **Complex fields:** `experience` (JSONB array), `education` (JSONB array), `skills` (JSONB array), `certifications` (JSONB array)  
- **System fields:** `id` (primary key), `createdAt` (timestamp)  

### User Interests Entity
- **Required fields:** `userId`  
- **Complex fields:** `topics` (JSONB array of strings), `skills` (JSONB array of strings)  
- **System fields:** `id` (primary key), `createdAt` (timestamp)  

### Career Goals Entity
- **Required fields:** `userId`  
- **Optional fields:** `desiredRole`, `industry`, `location`, `salaryRange`  
- **System fields:** `id` (primary key), `createdAt` (timestamp)  

### Saved Items Entity
- **Required fields:** `userId`, `itemType`, `itemId`, `itemData`  
- **Constraints:** `itemType` limited to `'person'`, `'job'`, `'course'`, `'post'`, or `'skill'`  
- **System fields:** `id` (primary key), `createdAt` (timestamp)  

### Users Entity (Auth)
- **Required fields:** `username` (unique), `password`  
- **System fields:** `id` (primary key)  

## Security Requirements

### Authentication
- System must authenticate users via username/password  
- Demo credentials: `username="demo"`, `password="password"`  
- Session management via `express-session` with `MemoryStore`  
- Authenticated sessions required for all API endpoints  

### Data Protection
- File uploads restricted to PDF MIME type (`application/pdf`)  
- File size limited to 5 MB maximum  
- Input validation on all API endpoints to prevent injection  
- Error messages sanitized to avoid information leakage  
- Environment variables used for sensitive values (`DATABASE_URL`, `SESSION_SECRET`)  

## Operational Requirements

### Deployment
- Application serves both API and static content on port 5000  
- Development mode uses Vite frontend dev server with TSX backend  
- Production builds frontend with Vite and bundles backend with esbuild  
- Environment variables required: `DATABASE_URL`, `SESSION_SECRET`  
- Database schema managed via Drizzle Kit migrations  

### Monitoring and Logging
- API request/response logging for monitoring and debugging  
- Error logging for troubleshooting  
- Client‑side React Query devtools for development inspection  

### Maintenance
- Component library updates via shadcn/ui  
- Type safety maintained through TypeScript  
- Database evolves via migration scripts  

## Assumptions and Limitations

### Current Implementation Notes
- User ID is hardcoded to 1 for all operations (single‑user demo)  
- Recommendation data is simulated/mocked rather than AI‑generated  
- PDF text extraction is simulated rather than using actual PDF parsing  
- Authentication uses a single demo user rather than multi‑user system  
- Storage falls back to in‑memory when database unavailable  

### Future Considerations
- Multi‑user support with proper user isolation  
- Real AI‑powered recommendation engine  
- Actual PDF text extraction using libraries like `pdf.js`  
- Enhanced security with role‑based access control  
- Real‑time updates via WebSocket connections  
- Extended file format support beyond PDF  
- Integration with actual LinkedIn API for data extraction
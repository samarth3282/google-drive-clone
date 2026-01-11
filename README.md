# 🗂️ StoreIt - AI-Powered Cloud Storage Platform

<div align="center">

![StoreIt Banner](https://img.shields.io/badge/StoreIt-AI%20Cloud%20Storage-FF6B6B?style=for-the-badge)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

**A modern, production-ready Google Drive clone with AI-powered file management capabilities**

[🎥 Watch Demo Video](#-demo-video) • [Live Demo](https://store-it-sp.vercel.app) • [Documentation](./DEPLOYMENT.md) • [Quick Start](./README-QUICKSTART.md)

Built by [Samarth Patel](https://github.com/samarth3282) & [Parth Goswami](https://github.com/ParthGoswami13)

</div>

---

## 📋 Table of Contents

- [Demo Video](#-demo-video)
- [Overview](#-overview)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [AI Agent Capabilities](#-ai-agent-capabilities)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

---

## 🎥 Demo Video

<div align="center">

<div style="position:relative; width:100%; height:0px; padding-bottom:56.250%"><iframe allow="fullscreen" allowfullscreen height="100%" src="https://streamable.com/e/q429my?" width="100%" style="border:none; width:100%; height:100%; position:absolute; left:0px; top:0px; overflow:hidden;"></iframe></div>

**Watch the complete walkthrough showcasing all features including AI-powered file management, RAG document analysis, and seamless UI/UX**

*Direct link: [View on Streamable](https://streamable.com/q429my)*

</div>

---

## 🌟 Overview

StoreIt is a cutting-edge cloud storage platform that combines the familiar interface of Google Drive with advanced AI capabilities. Unlike traditional storage solutions, StoreIt understands natural language, can analyze document content, and provides intelligent file management through an AI-powered assistant.

### Why StoreIt?

- 🤖 **AI-First Approach**: Natural language file operations
- 📚 **Document Intelligence**: Ask questions about your files using RAG (Retrieval-Augmented Generation)
- 🎨 **Modern UI/UX**: Beautiful, responsive interface with dark/light themes and 8 accent colors
- 🔐 **Secure**: Passwordless OTP authentication
- ⚡ **Real-time**: Instant file uploads and updates
- 🚀 **Production-Ready**: Deployed on Vercel + Render with comprehensive monitoring

---

## ✨ Key Features

### 🔐 Authentication
- **Passwordless OTP Authentication** - Secure email-based login with 6-digit verification codes
- **Session Management** - HTTP-only cookies for secure session handling
- **Auto-Login** - Seamless user experience with persistent sessions

### 📁 File Management
- **Drag & Drop Upload** - Intuitive file upload with progress tracking
- **File Organization** - Automatic categorization (Documents, Images, Media, Others)
- **Smart Search** - Real-time search with debounced queries
- **Advanced Sorting** - Sort by name, date, size (ascending/descending)
- **File Operations** - Rename, delete, share, download, view details
- **File Sharing** - Collaborate by sharing files with team members via email
- **Storage Analytics** - Visual dashboard with storage usage charts

### 🤖 AI-Powered Features
- **Natural Language Queries** - "Find all my PDFs", "Show me recent images"
- **Intelligent File Operations** - "Rename invoice.pdf to march-invoice.pdf", "Delete old files"
- **Document Analysis (RAG)** - Upload PDFs and ask questions about their content
- **Text File Reading** - AI can read and analyze text-based files (TXT, MD, JSON, CSV, XML)
- **Storage Insights** - "How much storage am I using?", "Show my storage breakdown"
- **Conversational Interface** - Chat-like interaction with streaming responses
- **Multi-turn Conversations** - Maintains context across multiple queries

### 🎨 UI/UX Features
- **Dynamic Theming** - Switch between light and dark modes with smooth animations
- **8 Accent Colors** - Personalize your experience (Pink, Blue, Purple, Green, Orange, Red, Teal, Indigo)
- **View Transitions API** - Smooth, native-like animations when changing themes/colors
- **Responsive Design** - Fully optimized for desktop, tablet, and mobile devices
- **File Thumbnails** - Intelligent preview generation for all file types
- **Loading States** - Beautiful skeleton loaders and progress indicators

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 15 (App Router, Server Components, Server Actions)
- **Language**: TypeScript
- **Styling**: Tailwind CSS, shadcn/ui components
- **State Management**: React Context API
- **UI Components**: Radix UI primitives
- **Icons**: Lucide React
- **Charts**: Recharts
- **Form Handling**: React Hook Form + Zod validation
- **Animations**: View Transitions API, CSS animations

### Backend
- **API Framework**: FastAPI (Python)
- **AI Orchestration**: LangChain, LangGraph
- **LLM**: Google Gemini 2.5 Flash
- **Embeddings**: Google text-embedding-004
- **Database**: Appwrite (BaaS)
- **File Storage**: Appwrite Storage
- **Vector Store**: Appwrite Collections (JSON-serialized vectors)
- **PDF Processing**: pdfplumber, Google Gemini (OCR fallback)

### DevOps & Monitoring
- **Frontend Hosting**: Vercel
- **Backend Hosting**: Render (Docker)
- **AI Monitoring**: LangSmith (tracing & observability)
- **Version Control**: Git, GitHub
- **Environment Management**: dotenv

---

## 📂 Project Structure

```
GDrive-clone/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Authentication routes (sign-in, sign-up)
│   ├── (root)/                   # Main application routes
│   │   ├── page.tsx              # Dashboard
│   │   └── [type]/               # File type pages (documents, images, media)
│   ├── api/                      # API routes
│   │   └── chat/                 # AI chat endpoint
│   ├── layout.tsx                # Root layout
│   └── globals.css               # Global styles
├── components/                   # React components
│   ├── AI/
│   │   └── ChatInterface.tsx     # AI chat UI
│   ├── ui/                       # shadcn/ui components
│   ├── AccentColorPicker.tsx     # Theme color selector
│   ├── AuthForm.tsx              # Sign-in/Sign-up form
│   ├── FileUploader.tsx          # File upload component
│   ├── Header.tsx                # Top navigation bar
│   ├── Sidebar.tsx               # Side navigation
│   ├── Search.tsx                # Search component
│   └── ...                       # Other UI components
├── lib/
│   ├── actions/                  # Server actions
│   │   ├── file.actions.ts       # File CRUD operations
│   │   └── user.actions.ts       # User authentication
│   ├── appwrite/                 # Appwrite configuration
│   └── utils.ts                  # Utility functions
├── ai-agent/                     # Python AI Backend
│   ├── agent.py                  # LangGraph agent definition
│   ├── main.py                   # FastAPI server
│   ├── tools.py                  # AI tools (8 custom tools)
│   ├── rag.py                    # RAG implementation
│   ├── context.py                # User context management
│   ├── Dockerfile                # Docker configuration
│   ├── requirements.txt          # Python dependencies
│   └── setup_rag.py              # RAG initialization script
├── contexts/                     # React contexts
│   └── AccentColorContext.tsx    # Theme management
├── constants/                    # App constants
├── types/                        # TypeScript type definitions
├── public/                       # Static assets
├── DEPLOYMENT.md                 # Deployment guide
├── LANGSMITH-SETUP.md            # LangSmith integration guide
└── README-QUICKSTART.md          # Quick start guide
```

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** 18+ 
- **Python** 3.11+
- **Appwrite Account** ([Sign up](https://appwrite.io))
- **Google AI API Key** ([Get one](https://aistudio.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/samarth3282/google-drive-clone.git
   cd google-drive-clone
   ```

2. **Install Frontend Dependencies**
   ```bash
   npm install
   ```

3. **Install Backend Dependencies**
   ```bash
   cd ai-agent
   pip install -r requirements.txt
   cd ..
   ```

4. **Configure Environment Variables**
   ```bash
   cp .env.example .env.local
   ```
   
   Edit `.env.local` with your credentials:
   ```env
   # Appwrite Configuration
   NEXT_PUBLIC_APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
   NEXT_PUBLIC_APPWRITE_PROJECT=your_project_id
   NEXT_PUBLIC_APPWRITE_DATABASE=your_database_id
   NEXT_PUBLIC_APPWRITE_USERS_COLLECTION=your_users_collection_id
   NEXT_PUBLIC_APPWRITE_FILES_COLLECTION=your_files_collection_id
   NEXT_PUBLIC_APPWRITE_BUCKET=your_bucket_id
   NEXT_APPWRITE_KEY=your_api_key
   
   # Google AI
   GOOGLE_API_KEY=your_google_api_key
   
   # Vector Collection
   VECTOR_COLLECTION_ID=your_vector_collection_id
   
   # FastAPI URL (for production)
   FASTAPI_URL=http://localhost:8000
   
   # Optional: LangSmith (AI Monitoring)
   LANGCHAIN_TRACING_V2=false
   LANGCHAIN_API_KEY=your_langsmith_key
   LANGCHAIN_PROJECT=gdrive-clone
   ```

5. **Run the Development Servers**

   **Terminal 1 - Next.js Frontend:**
   ```bash
   npm run dev
   ```
   → Runs on http://localhost:3000

   **Terminal 2 - FastAPI Backend:**
   ```bash
   cd ai-agent
   python main.py
   ```
   → Runs on http://localhost:8000

6. **Access the Application**
   - Open http://localhost:3000
   - Sign up with your email
   - Enter the OTP code sent to your email
   - Start uploading and managing files!

### Quick Setup Guide

For a detailed step-by-step guide, see [README-QUICKSTART.md](./README-QUICKSTART.md)

---

## 🤖 AI Agent Capabilities

The AI agent is powered by **LangGraph** and **Google Gemini 2.5 Flash**, featuring 8 custom tools:

### 1. 🔍 **search_files**
Search for files by name or type
```
User: "Find all my PDF files"
AI: Lists all PDF files with details
```

### 2. ✏️ **rename_file**
Rename files using natural language
```
User: "Rename invoice.pdf to march-invoice.pdf"
AI: File successfully renamed
```

### 3. 🗑️ **delete_file**
Delete files securely
```
User: "Delete old-document.pdf"
AI: File deleted successfully
```

### 4. 🔗 **share_file**
Share files with team members
```
User: "Share presentation.pptx with john@example.com"
AI: File shared with john@example.com
```

### 5. 📊 **get_storage_stats**
Get storage usage statistics
```
User: "How much storage am I using?"
AI: Total storage used: 450MB / 2GB
```

### 6. 📄 **read_file_content**
Read text-based file content
```
User: "What's in notes.txt?"
AI: [Displays file content]
```

### 7. 🧠 **process_file_for_search** (RAG)
Process PDFs for intelligent Q&A
```
User: "Analyze research-paper.pdf"
AI: File processed. 15 chunks indexed.
```

### 8. 💬 **ask_file_question** (RAG)
Ask questions about processed documents
```
User: "What are the key findings in the research paper?"
AI: [Provides accurate answers based on document content]
```

### RAG (Retrieval-Augmented Generation) Features

- **Automatic Text Extraction**: Uses pdfplumber for standard PDFs
- **OCR Fallback**: Google Gemini for scanned/image-based PDFs
- **Vector Embeddings**: Google text-embedding-004 model
- **Semantic Search**: Cosine similarity for relevant chunk retrieval
- **Context-Aware**: Provides accurate answers based on document content

---

## 🎨 Screenshots & Demo

> 💡 **Tip**: Watch the [full demo video](#-demo-video) at the top to see all features in action!

### Dashboard
![Dashboard](./demo/screenshots/dashboard.png)

### AI Chat Interface
![AI Chat](./demo/screenshots/ai-chat.png)

### File Management
![File Management](./demo/screenshots/file-management.png)

### Theme Customization
![Themes](./demo/screenshots/themes.png)

---

## 📦 Deployment

### Production Deployment

StoreIt is deployed using:
- **Frontend**: Vercel (Next.js)
- **Backend**: Render (FastAPI with Docker)
- **Database**: Appwrite Cloud

For detailed deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md)

### Quick Deploy

1. **Deploy Frontend to Vercel**
   ```bash
   vercel --prod
   ```

2. **Deploy Backend to Render**
   - Connect GitHub repository
   - Set root directory to `ai-agent`
   - Use Docker runtime
   - Add environment variables

3. **Configure CORS**
   Update `ALLOWED_ORIGINS` in Render with your Vercel URL

---

## 🔧 Configuration

### Appwrite Setup

1. Create a new project in [Appwrite Console](https://cloud.appwrite.io)
2. Create database with collections:
   - **Users Collection**: fullName, email, avatar, accountId
   - **Files Collection**: name, type, size, url, owner, users, bucketFileId
   - **Vector Collection**: file_id, content, embedding
3. Create storage bucket
4. Add platform (your domain)

### LangSmith Integration (Optional)

For AI monitoring and tracing, see [LANGSMITH-SETUP.md](./LANGSMITH-SETUP.md)

---

## 🧪 Testing

```bash
# Run frontend tests
npm run lint

# Check AI agent health
curl http://localhost:8000/health
```

---

## 📚 Documentation

- [Quick Start Guide](./README-QUICKSTART.md) - Get started in 5 minutes
- [Deployment Guide](./DEPLOYMENT.md) - Production deployment steps
- [LangSmith Setup](./LANGSMITH-SETUP.md) - AI monitoring configuration
- [Pre-Deployment Checklist](./PRE-DEPLOYMENT-CHECKLIST.md) - Before going live

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 🐛 Known Issues & Troubleshooting

### Common Issues

1. **CORS Error in Browser**
   - Ensure `ALLOWED_ORIGINS` includes your frontend URL
   - Check FastAPI CORS middleware configuration

2. **AI Agent Not Responding**
   - Verify `GOOGLE_API_KEY` is valid
   - Check Appwrite credentials
   - Ensure FastAPI server is running

3. **File Upload Fails**
   - Check file size (max 50MB)
   - Verify Appwrite bucket permissions
   - Check network connectivity

4. **Render Free Tier Slowness**
   - Free tier spins down after 15 min inactivity
   - First request takes 30-60s to wake up
   - Upgrade to paid plan for always-on service

For more troubleshooting tips, see [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## 📈 Future Enhancements

- [ ] Folder organization and nested structures
- [ ] Advanced file versioning
- [ ] Real-time collaborative editing
- [ ] File preview (PDF, images, videos)
- [ ] Bulk operations (multi-file upload/delete)
- [ ] Advanced search filters
- [ ] File compression and optimization
- [ ] Mobile app (React Native)
- [ ] Integration with third-party services (Google Drive, Dropbox)
- [ ] Advanced AI features (auto-tagging, content summarization)

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

**Samarth Patel**
- GitHub: [@samarth3282](https://github.com/samarth3282)
- LinkedIn: [Samarth Patel](https://www.linkedin.com/in/samarthnimeshkumarpatel/)

**Parth Goswami**
- GitHub: [@parthgoswami]()
- LinkedIn: [Parth Goswami]()

---

## 🙏 Acknowledgments

- [Next.js](https://nextjs.org/) - React framework
- [FastAPI](https://fastapi.tiangolo.com/) - Python web framework
- [LangChain](https://www.langchain.com/) - LLM framework
- [Google Gemini](https://deepmind.google/technologies/gemini/) - AI model
- [Appwrite](https://appwrite.io/) - Backend-as-a-Service
- [Vercel](https://vercel.com/) - Frontend hosting
- [Render](https://render.com/) - Backend hosting
- [shadcn/ui](https://ui.shadcn.com/) - UI components

---

## ⭐ Show Your Support

If you found this project helpful or interesting, please consider giving it a star ⭐ on GitHub!

---

<div align="center">

**Built with ❤️ by Samarth Patel & Parth Goswami**

[⬆ Back to Top](#️-storeit---ai-powered-cloud-storage-platform)

</div>

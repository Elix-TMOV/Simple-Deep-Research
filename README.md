Video Demo: https://youtu.be/-CGlkX2A8NQ

### Build using the standard client-server architecture

Frontend

* Built with React + TypeScript + Vite
* Uses Material-UI (MUI) for styled components
* Non trivial featurers Include
   * Markdown rendering of research reports with react-markdown
   * PDF export functionality via html2pdf.js

Backend 
* Built with FastAPI (Python)
* Uses LangChain to implement the AI workflow
* Key components
  * Google's Gemini api for text generation
  * Tavily Search API for web research
  * Structured workflow using LangGraph

Core Workflow
1. User enters a research topi
2. Backend generates clarifying questions using Gemini AI
3. User provides answers to questions
4. Backend creates a research workflow:
5. Generates focused search queries
6. Executes web searches via Tavily
7. Synthesizes findings into a comprehensive report
8. Frontend displays the formatted report with options to save as PDF


The genereate_clarifying_question is a sepereate api endpoint and not part of the workflow graph



  

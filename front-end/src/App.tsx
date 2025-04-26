import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { createRef } from 'react'
import { 
  Box, 
  TextField, 
  Button, 
  Card, 
  Typography,
  Container,
  Stack
} from '@mui/material'
import axios from 'axios'

import html2pdf from 'html2pdf.js';

type QA = {
  question: string;
  answer: string;
}



function App() {
  const [loading, setLoading] = useState(false)
  const [userInput, setUserInput] = useState('')
  const [showQuestions, setShowQuestions] = useState(false)
  const [qaList, setQaList] = useState<QA[]>([])
  const [report, setReport] = useState<string | null>(null)
  const pdfRef = createRef<HTMLDivElement>()

  const get_clarifying_questions = async (userInput: string) => {
    try {
      setLoading(true)
      const response = await axios.post<string[]>(
        'http://localhost:8000/api/ai/get_carifying_questions',
        { user_query: userInput }
      )
      // Initialize QA list with empty answers
      const questions = response.data
      const initialQa = questions.map(q => {
        return { question: q, answer: '' }
      })

      setQaList(initialQa)
      setLoading(false)
      setShowQuestions(true)
    } catch (error) {
      setLoading(false)
      console.error('Error fetching questions:', error)
    }
  }

  const handleDownloadPDF = () => {
      if (pdfRef.current) {
        html2pdf().from(pdfRef.current).save()
      }
    }

  const handleMainSubmit = async () => {

    await get_clarifying_questions(userInput)
  }

  const handleQuestionSubmit = async () => {
    // Build a dictionary mapping questions to answers
    setShowQuestions(false)
    setLoading(true)
    console.log('QA Dictionary:', qaList)
    try{
      const response = await axios.post('http://localhost:8000/api/ai/get_report', {
        user_query: userInput,
        qaList: qaList 
      })
      setReport(response.data)
      setLoading(false)
    }
    catch (error) {
      setLoading(false)
      console.error('Error creating the report:', error)
    }
    // You can now send qaDict to your backend or use it as needed
  }

  const handleAnswerChange = (index: number, e: React.ChangeEvent<HTMLInputElement>) => {
    // never change the original state directly so we create a copy of it
    const newQaList = [...qaList]
    newQaList[index] = { ...newQaList[index], answer: e.target.value }
    setQaList(newQaList)
  }


  return (
    <Box sx={{ 
      minHeight: '100vh', 
      backgroundColor: '#121212',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
    }}>
      <Typography
        variant="h2"
        sx={{
          background: 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)',
          backgroundClip: 'text',
          textFillColor: 'transparent',
          marginBottom: 4
        }}
      >
        Deep Research
      </Typography>

      <Container maxWidth="md">
        <TextField
          fullWidth
          multiline
          rows={4}
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          variant="outlined"
          placeholder="Enter your research topic..."
          sx={{ 
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
            borderRadius: 1,
            '& .MuiOutlinedInput-root': {
              color: 'white'
            }
          }}
        />
        <Button 
          variant="contained"
          onClick={handleMainSubmit}
          sx={{ 
            mt: 2,
            background: 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)'
          }}
        >
          Submit
        </Button>
      </Container>

      {loading && (
        <Typography variant="body1" sx={{ mt: 2, color: 'white' }}>
          Loading...
        </Typography>
      )}

      {!loading && !showQuestions && (
        <Typography variant="body1" sx={{ mt: 2, color: 'white' }}>
          Please enter a research topic to get started.
        </Typography>
      )}

      {showQuestions && (
        <Card sx={{ 
          mt: 4, 
          p: 3, 
          width: '100%', 
          maxWidth: 600,
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
          color: 'white'
        }}>
          <Typography variant="h5" sx={{ mb: 2 }}>
            Please answer the following questions, to better understand your research topic:
          </Typography>
          <Stack spacing={2}>
            {qaList.map((qa, index) => (
              <Container key={index}>
                <Typography
                  variant="body1"
                  sx={{
                    color: 'white',
                    mb: 1,
                    background: 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)',
                    backgroundClip: 'text',
                    textFillColor: 'transparent'
                  }}
                >
                  {qa.question}
                </Typography>
                <TextField
                  fullWidth
                  value={qa.answer}
                  onChange={(e) => {
                    handleAnswerChange(index, e)
                  }}
                  placeholder="Your answer..."
                  sx={{ 
                    '& .MuiOutlinedInput-root': {
                      color: 'white'
                    }
                  }}
                />
              </Container>
            ))}
            <Button 
              variant="contained"
              onClick={handleQuestionSubmit}
              sx={{ 
                background: 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)'
              }}
            >
              Submit Answers
            </Button>
          </Stack>
        </Card>
      )}

      {report && (
        <Card sx={{ 
          mt: 4, 
          p: 3, 
          width: '100%', 
          maxWidth: 800,
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
          color: 'white',
          fontFamily: "arial, sans-serif",
        }}>
          <Container
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 2,
          }}
          >
            <Typography variant="h5" sx={{ mb: 2 }}>
              Generated Report
            </Typography>
            <Button
              onClick={handleDownloadPDF}
              sx={{ 
                color: 'white',
                background: 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)'
              }}
            >
              Save as pdf
            </Button>
          </Container>
          <div ref={pdfRef} style={{ padding: '20px' }}>
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({node, ...props}) => (
                  <Typography variant="h4" sx={{ color: '#FE6B8B', mb: 2 }} {...props} />
                ),
                h2: ({node, ...props}) => (
                  <Typography variant="h5" sx={{ color: '#FF8E53', mb: 2 }} {...props} />
                ),
                p: ({node, ...props}) => (
                  <Typography variant="body1" sx={{ mb: 2 }} {...props} />
                ),
                a: ({node, ...props}) => (
                  <a style={{ color: '#FF8E53' }} {...props} />
                ),
                code: ({node, ...props}) => (
                  <code style={{ 
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    padding: '2px 4px',
                    borderRadius: '4px'
                  }} {...props} />
                )
              }}
            >
              {report}
            </ReactMarkdown>
          </div>
        
        </Card>
      )}
    </Box>
  )
}

export default App

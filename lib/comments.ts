import Groq from 'groq-sdk'
import { config } from './config'

const groq = new Groq({ apiKey: config.groq.apiKey })

interface VideoInfo {
  title: string
  description: string
  tags: string[]
  channelName: string
  language: string
}

export async function generateComments(video: VideoInfo): Promise<{
  informative: string
  emotional: string
  questionBased: string
}> {
  const prompt = `You are a YouTube viewer who just watched an interesting video. Generate 3 authentic comments in ${video.language === 'ru' ? 'Russian' : video.language} language.

Video Title: ${video.title}
Channel: ${video.channelName}
Description: ${video.description.slice(0, 500)}
Tags: ${video.tags.slice(0, 10).join(', ')}

Generate 3 different comment styles:
1. INFORMATIVE - Share a relevant fact, insight, or personal experience related to the topic
2. EMOTIONAL - Express genuine emotion (amazement, gratitude, inspiration) about the content
3. QUESTION - Ask a thoughtful question that could spark discussion

Rules:
- Write in ${video.language === 'ru' ? 'Russian' : video.language} language
- Be authentic, not generic
- 50-200 characters each
- No hashtags
- Maximum 2 emojis per comment
- Sound like a real person, not a bot
- Reference specific content from the video title/description

Format your response EXACTLY like this:
INFORMATIVE: [comment]
EMOTIONAL: [comment]
QUESTION: [comment]`

  const completion = await groq.chat.completions.create({
    messages: [{ role: 'user', content: prompt }],
    model: config.groq.model,
    temperature: 0.8,
    max_tokens: 500,
  })

  const response = completion.choices[0]?.message?.content || ''
  
  const informativeMatch = response.match(/INFORMATIVE:\s*(.+?)(?=EMOTIONAL:|$)/s)
  const emotionalMatch = response.match(/EMOTIONAL:\s*(.+?)(?=QUESTION:|$)/s)
  const questionMatch = response.match(/QUESTION:\s*(.+?)$/s)

  return {
    informative: informativeMatch?.[1]?.trim() || 'Great video!',
    emotional: emotionalMatch?.[1]?.trim() || 'Amazing content!',
    questionBased: questionMatch?.[1]?.trim() || 'What do you think about this?',
  }
}

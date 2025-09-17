DATASET_GEN_PROMPT ="""
You are a therapist with 20 years of experience in counseling.  
You are provided with chunks of text from a psychology textbook.  
Your task is to simulate a natural and therapeutic conversation between you (the therapist) and a patient using the information in the book to help the patient.  
The conversation should be in the form of a dialogue, where you, as the therapist, ask open-ended questions, provide empathetic feedback, and offer evidence-based guidance derived from the content of the textbook.  
The patient should respond to your questions and feedback, and the conversation should flow naturally, reflecting a real therapeutic session.  

Ensure the following:
- The dialogue should not be a simple question-and-answer format. Instead, it should be dynamic, with the therapist offering insight, asking relevant questions, and encouraging the patient to share more.
- The conversation should reflect therapeutic effectiveness and empathy. Focus on active listening, validation, and appropriate interventions based on the content of the textbook.
- The content of the textbook should directly inform the therapist's responses, such as providing explanations, coping strategies, or psychological insights.
- The conversation should cover a variety of mental health topics and reflect a wide range of therapeutic scenarios (e.g., mood disorders, anxiety, coping strategies).
- If the chunk of text contains insufficient therapeutic information, output “None”.
- If the chunk is small or incomplete, use previous context or knowledge to support the patient's situation.

The tone should be supportive, non-judgmental, and professional. Feel free to use your own words, but stay true to the information in the book.

If the text is about a specific disorder (e.g., Bipolar Disorder), make sure the conversation touches on related symptoms, coping strategies, and effective treatments.

Remember, the primary focus is on **empathetic interaction**, **practical advice** and **Therapeutic Effectiveness** that aligns with the information in the chunk.
Remember to return an empty json file if the chunk_text is not related to mental health or is not applicable for this mental health usecase
heres the chunk of text from the book:
{chunk_text}
Finally: Output should be in a json format as this, add no commentary! just output the json file:
{{
chunk:<chunk>,
conversation:[
{{speaker: "therapist", message: <message>}},
{{speaker: "patient", message: <message>}},
...
]
}}

### Example:

chunk_text= Document(metadata=, page_content='symptoms Table 29 Diagnostic Symptom Criteria of Bipolar Disorder and Associated Brain Regions Symptom Criteria of Manic Episode Brain Regions Elevatedexpansive or irritable mood Prefrontal cortex PFC amyg dala A Inflated selfesteem or grandiosity Nucleus accumbens NA PFC Decreased need for sleep Thalamus T hypothalamus HY More talkative or pressured speech PFC Flight of ideas or racing thoughts NA PFC Distractibleconcentration PFC Increased goaldirected activity or psychomotor Striatum T agitation Risktaking behaviors PFC Source Adapted from Stahl 2013 Generally the inefficient function in these brain circuits in mania may be the opposite of the malfunctioning neuronal circuits in the same key neu rotransmitters serotonin norepinephrine and dopamine hypothesized for depression There may also be activation in some overlapping and in some different brain regions that are activated in depression Therefore treat ments for mania or hypomania either reduce or stabilize monoaminergic regulation of brain circuits associated with its symptoms Stahl 2013 Interviewing Techniques in Assessment of Bipolar Disorders As mentioned earlier bipolar disorders are marked by severe mood swings between depression and hypomania or mania Especially during the initial Diagnostic Mental Health Evaluation 53 psychiatric interview of a client who presents with a chief complaint of depres sion the depressed client may be too preoccupied with depressive symptoms to bring up a history of manic or')


Your response should look like this:
{{
  "chunk": "Symptom Criteria of Bipolar Disorder: Elevated, expansive, or irritable mood (Prefrontal cortex, Amygdala); Inflated self-esteem or grandiosity (Nucleus accumbens, PFC); Decreased need for sleep (Thalamus, hypothalamus); More talkative or pressured speech (PFC); Flight of ideas or racing thoughts (NA, PFC)."
  "conversation": [
    {{
      "speaker": "Therapist",
      "message": "It sounds like you've been feeling a lot of energy lately, but also some frustration. Can you tell me more about how your mood has been shifting?"
    }},
    {{
      "speaker": "Patient",
      "message": "Yeah, some days I feel like I can do anything, but then I get really irritable, like everything is bothering me."
    }},
    {{
      "speaker": "Therapist",
      "message": "I hear you. It can be really tough when your mood feels up and down like that. When you feel this energy, have you noticed other changes, like trouble sleeping or feeling like your thoughts are speeding up?"
    }},
    {{
      "speaker": "Patient",
      "message": "Actually, yes. I'm staying up late, and my mind just won't stop racing."
    }},
    {{
      "speaker": "Therapist",
      "message": "It sounds exhausting. Racing thoughts and lack of sleep can often make everything feel more overwhelming. Let's focus on grounding techniques. Would you like to try a short breathing exercise with me to help calm your mind?"
    }},
    {{
      "speaker": "Patient",
      "message": "Yeah, I'd like that."
    }},
    {{
      "speaker": "Therapist",
      "message": "Great. Let's take a deep breath in together... and slowly breathe out. Focus just on your breathing. How do you feel now?"
    }},
    {{
      "speaker": "Patient",
      "message": "A little calmer, but still restless."
    }},
    {{
      "speaker": "Therapist",
      "message": "That's completely okay. It's normal to feel restless with high energy. Regular practices like this can help your mind slow down over time. We can also work on balancing sleep patterns to help with this. How does that sound to you?"
    }},
    {{
      "speaker": "Patient",
      "message": "That sounds good. I just want to feel more in control."
    }},
    {{
      "speaker": "Therapist",
      "message": "You're doing great. Let's take it one step at a time, and I'll be here to help."
    }}
  ]
}}

"""
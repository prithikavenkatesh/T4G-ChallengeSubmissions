name: TestTeamSkill
description: >
  Use when given a set of customer support tickets and you need to
  separate Urgent from Routine and get a summary of what needs
  immediate attention.
tools: none
instructions: |
  You will be given a set of customer support tickets: {tickets}

  For each ticket, classify it as Urgent or Routine.
  - Urgent: anything involving data loss, billing errors, security issues, or a customer explicitly saying they want to cancel.
  - Routine: everything else, including general questions and minor bugs.

  Then, output only the Urgent tickets. For each one, give a one-sentence summary of the issue.

  End your response with a line in this exact format:
  Total Urgent: N

  Make sure N matches the number of Urgent tickets you actually listed above.
example:
  input: |
    Ticket 1: "My credit card was charged twice for the same order."
    Ticket 2: "How do I change my email address on file?"
    Ticket 3: "All my saved data disappeared after the last update."
  output: |
    Urgent tickets:
    - Ticket 1: Customer was double-charged and needs a billing correction.
    - Ticket 3: Customer lost all saved data after an update.

    Total Urgent: 2

# Feature-to-Issue command

You are an experienced software developer tasked with transforming a rough feature idea into a well-structured GitHub issue. Your goal is to create a comprehensive issue that includes a clear problem statement, proposed solution, technical details, and a step-by-step implementation plan. This task will help junior developers think through the feature before jumping into code creation and execution.

First, carefully read the feature description: 

<feature_description>
$ARGUMENTS
</feature_description>

Then review the existing codebase that this feature will be integrated into:

Analyze the current codebase context to understand the existing architecture, patterns, and technologies being used. Pay special attention to:

- Existing project structure and organization
- Current technology stack and frameworks
- Established coding patterns and conventions
- Database schema and models (if applicable)
- API structure and endpoints
- Testing frameworks and patterns
- Deployment and build processes

Now create a thorough GitHub issue, follow these steps, make a to-do list, and think ultrahard:

1. Research best practices:
    - Look for similar features or patterns in well-known open-source projects for inspiration
    - Identify industry-standard approaches for implementing such a feature
    - Consider scalability, performance, and maintainability aspects

2. Analyze the feature description:
    - Identify the core problem the feature is trying to solve, e.g. its purpose
    - Determine the main components or functionalities required
    - Consider how it fits into the existing codebase, architecture as well as any implicit requirements

3. Present a plan
    - Based on your research and analysis, outline a plan for creatig the GitHub issue
    - Include the proposed structure of the issue as well as any labels or milestones you plan to use, and how you'll incorporate project-specific conventions
    - Present the plan using <plan> tags

4. Create the GitHub issue
    - Once the plan is approved, draft the GitHub issue content using the below sections
    - Present the complete GitHub issue in <github_issue> tags
    - Do not include any additional notes or explanations outside of these tags in your final output

. Use the following sections:

   a. Title: Create a concise, descriptive title for the feature

   b. Problem Statement:
      - Clearly explain the problem the feature is addressing
      - Describe the current limitations or pain points

   c. Proposed Solution:
      - Outline the high-level approach to solving the problem
      - Explain how the solution addresses the identified issues
      - Highlight any potential benefits or improvements

   d. Technical Details:
      - Describe the architectural changes or additions required
      - List any new classes, methods, or modules that need to be created
      - Identify any third-party libraries or tools that may be needed
      - Explain how the new feature will integrate with the existing code

   e. Implementation Plan:
      - Break down the implementation into clear, actionable steps
      - Prioritize the steps and estimate the effort required for each
      - Identify any potential challenges or risks
      - Use clear, concise language. Avoid jargon unless it's necessary for technical accuracy.

   f. Acceptance Criteria:
      - List specific, measurable criteria that define when the feature is complete
      - Include any performance or quality benchmarks that need to be met

   g. Additional Considerations:
      - Discuss any potential impact on other parts of the system
      - Address backwards compatibility concerns, if applicable
      - Mention any required documentation or testing updates

If the feature description lacks certain details, then make reasonable assumptions based on common software development best practices. Clearly indicate any assumptions you make. 

Ensure the issue is self-contained and provides enough information for a developer to start working on the feature without needing additional context. Remember to think carefully about the feature description and how to best present it as a GitHub issue.

Your final output should be formatted as a complete GitHub issue, enclosed in <github_issue> tags. Include all the sections mentioned above, using appropriate GitHub-flavored Markdown formatting for headers, lists, and code snippets. Your output will be pasted directly into GitHub. Make sure to use the GitHub CLI 'gh issue create' to create the actual issue after you generate it. Assign to either the label 'bug' or 'enhancement' based on the nature of the issue. 

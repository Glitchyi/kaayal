# Owner review decisions

## Already settled
- Name: Kaayal (കായൽ), entire product and voice agent.
- A Sarvam number has already been provisioned by the owner.
- OpenAI API credits exist and should be used through a FastAPI tool.
- Phase 1 is **phone call + generated spoken reply only**.
- Phase 2 may explore Alappuzha operators, operator tools and tourism workflows after clarification.
- No Iroh/P2P; avoid infrastructure overhead.

## Need to check before first live call
1. Is the provisioned number visible under Sarvam's inbound phone deployments? If not, which dashboard workflow is available?
2. Does the active Sarvam plan support outbound HTTPS tool requests and custom auth headers?
3. Which Sarvam voice agent model/language combination speaks Malayalam well?
4. What exact OpenAI text model is available under the owner's account? Default is only a nonsecret suggestion.
5. Which secure HTTPS tunnel can owner expose from Mac and update in Sarvam dashboard?
6. Is the user willing to place and observe a live test call? Required for real end-to-end verification.

Do not ask for phone number, secrets, or other sensitive values in chat; use protected environment variables or platform settings.

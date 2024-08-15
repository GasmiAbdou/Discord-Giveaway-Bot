# Discord Giveaway Bot 🎉

Welcome to the Discord Giveaway Bot! This powerful and feature-rich bot allows you to effortlessly manage giveaways on your Discord server. With customizable settings, multiple entry requirements, and an intuitive interface, hosting giveaways has never been easier!

## Features 🚀

- **Easy Giveaway Creation**: Start giveaways with a simple slash command
- **Customizable Duration**: Set giveaway duration using flexible time formats (e.g., 1h 30m, 2d)
- **Multiple Winners**: Support for multiple winners in a single giveaway
- **Entry Requirements**: 
  - Role-based entry restrictions
  - Server membership requirements
  - Entry limits to control participation
- **Customizable Embeds**: Personalize your giveaway announcements with custom colors, images, and more
- **Interactive Buttons**: Users can join giveaways with a single click
- **Participant Viewing**: Easily view and manage giveaway participants
- **Reroll Function**: Ability to reroll winners for ended giveaways
- **Giveaway Cancellation**: Option to cancel ongoing giveaways
- **Active Giveaway Listing**: View all active giveaways across your server
- **Automatic Ending**: Giveaways automatically end and announce winners

## Installation 🛠️

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/discord-giveaway-bot.git
   ```

2. Navigate to the project directory:
   ```
   cd discord-giveaway-bot
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory and add your Discord bot token:
   ```
   DISCORD_TOKEN=your_bot_token_here
   ```

5. Run the bot:
   ```
   python main.py
   ```

## Usage 📚

### General Commands

- `/help`: Display help information and command usage
- `/list`: Show all active giveaways

### Giveaway Commands

- `/giveaway`: Start a new giveaway
- `/reroll`: Reroll winners for the last ended giveaway
- `/cancel`: Cancel the current giveaway in the channel

### Admin Commands

- `/refresh`: Manually refresh slash commands (Admin only)
- `/giveaway_settings`: Customize your giveaway message appearance

### Starting a Giveaway

1. Use the `/giveaway` command
2. Fill in the required information:
   - Prize
   - Duration
   - Number of Winners
   - Additional Notes (optional)
3. Choose requirements (if any):
   - Role Requirement
   - Server Requirement
4. Confirm and launch!

## Contributing 🤝

Contributions are welcome! Please feel free to submit a Pull Request.



## Support 💬

If you encounter any issues or have questions, please open an issue on GitHub or contact the maintainer. Or join the discord server [GHOSTFACE](https://discord.gg/qEjYs7sSad)

---

Enjoy hosting amazing giveaways with your Discord Giveaway Bot! 🎊

import os
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

# Conversation states
FILE, NAME, COUNT, NUMBERS_PER_FILE, CONTACT_PREFIX = range(5)

def start(update: Update, context: CallbackContext):
    """Starts the conversation and asks the user to send a .txt file."""
    update.message.reply_text("Send a .txt file containing phone numbers.")
    return FILE

def file_handler(update: Update, context: CallbackContext):
    """Handles the file sent by the user."""
    file = update.message.document
    if not file.file_name.endswith('.txt'):
        update.message.reply_text("Please send a valid .txt file.")
        return FILE
    
    file_path = f"downloads/{file.file_name}"
    os.makedirs("downloads", exist_ok=True)
    
    try:
        file.get_file().download(file_path)
        context.user_data['file_path'] = file_path
    except Exception as e:
        update.message.reply_text(f"Failed to download file: {e}")
        return ConversationHandler.END
    
    update.message.reply_text("Enter the base file name (e.g., 'me'):")
    return NAME

def name_handler(update: Update, context: CallbackContext):
    """Handles the base file name."""
    base_name = update.message.text.strip()
    if not base_name:
        update.message.reply_text("Please enter a valid base file name.")
        return NAME
    context.user_data['base_name'] = base_name
    update.message.reply_text("How many .vcf files should be created?")
    return COUNT

def count_handler(update: Update, context: CallbackContext):
    """Handles the number of .vcf files to be created."""
    try:
        file_count = int(update.message.text.strip())
        if file_count <= 0:
            raise ValueError("Number of files must be greater than 0.")
        context.user_data['file_count'] = file_count
        update.message.reply_text("How many numbers should be in each .vcf file?")
        return NUMBERS_PER_FILE
    except ValueError as e:
        update.message.reply_text(f"Invalid input. {e}")
        return COUNT

def numbers_per_file_handler(update: Update, context: CallbackContext):
    """Handles how many numbers should be in each .vcf file."""
    try:
        numbers_per_file = int(update.message.text.strip())
        if numbers_per_file <= 0:
            raise ValueError("Number of contacts per file must be greater than 0.")
        context.user_data['numbers_per_file'] = numbers_per_file
        update.message.reply_text("Enter the contact name prefix (e.g., 'contact'):")
        return CONTACT_PREFIX
    except ValueError as e:
        update.message.reply_text(f"Invalid input. {e}")
        return NUMBERS_PER_FILE

def contact_prefix_handler(update: Update, context: CallbackContext):
    """Handles the contact name prefix."""
    contact_prefix = update.message.text.strip()
    if not contact_prefix:
        update.message.reply_text("Please enter a valid contact name prefix.")
        return CONTACT_PREFIX
    context.user_data['contact_prefix'] = contact_prefix

    file_path = context.user_data['file_path']
    base_name = context.user_data['base_name']
    file_count = context.user_data['file_count']
    numbers_per_file = context.user_data['numbers_per_file']
    
    try:
        with open(file_path, 'r') as f:
            numbers = [line.strip() for line in f if line.strip()]
    except Exception as e:
        update.message.reply_text(f"Error reading the file: {e}")
        return ConversationHandler.END
    
    if len(numbers) < file_count * numbers_per_file:
        update.message.reply_text("Not enough numbers in the file. Adjust the input values.")
        return ConversationHandler.END
    
    for i in range(file_count):
        vcf_filename = f"{base_name} {i+1}.vcf"
        try:
            with open(f"downloads/{vcf_filename}", 'w') as vcf:
                for j in range(numbers_per_file):
                    index = i * numbers_per_file + j
                    vcf.write(f"BEGIN:VCARD\nVERSION:3.0\nFN:{contact_prefix} {index+1}\nTEL:{numbers[index]}\nEND:VCARD\n")
            update.message.reply_document(InputFile(f"downloads/{vcf_filename}"))
        except Exception as e:
            update.message.reply_text(f"Error creating VCF file {vcf_filename}: {e}")
            return ConversationHandler.END
    
    update.message.reply_text("All .vcf files have been created and sent!")
    return ConversationHandler.END

def main():
    """Main function to start the bot."""
    BOT_TOKEN = os.getenv("7485450093:AAH5hJMgpZbLlGPqtQmetBgULl3zeoxSXV8")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set!")
    
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FILE: [MessageHandler(Filters.document, file_handler)],
            NAME: [MessageHandler(Filters.text, name_handler)],
            COUNT: [MessageHandler(Filters.text, count_handler)],
            NUMBERS_PER_FILE: [MessageHandler(Filters.text, numbers_per_file_handler)],
            CONTACT_PREFIX: [MessageHandler(Filters.text, contact_prefix_handler)],
        },
        fallbacks=[]
    )
    
    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

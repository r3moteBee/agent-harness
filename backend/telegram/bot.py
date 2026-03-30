"""Telegram bot integration using python-telegram-bot."""
from __future__ import annotations
import asyncio
import logging
from typing import Any

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_application: Any = None


async def start_telegram_bot() -> None:
    """Initialize and start the Telegram bot."""
    global _application
    if not settings.telegram_bot_token:
        logger.info("Telegram bot token not configured, skipping.")
        return

    try:
        from telegram import Update
        from telegram.ext import (
            Application,
            CommandHandler,
            MessageHandler,
            filters,
            ContextTypes,
        )

        app = Application.builder().token(settings.telegram_bot_token).build()

        async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            if not _is_allowed(update):
                return
            await update.message.reply_text(
                "Hello! I'm your Agent Harness AI assistant.\n\n"
                "Commands:\n"
                "/chat <message> — Send a message to the agent\n"
                "/project <name> — Switch active project\n"
                "/status — Get agent status\n"
                "/files — List workspace files\n"
                "/task <description> — Create an autonomous task\n"
                "/memory <query> — Search memories"
            )

        async def chat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            if not _is_allowed(update):
                return
            message = " ".join(context.args) if context.args else ""
            if not message:
                await update.message.reply_text("Usage: /chat <your message>")
                return

            await update.message.reply_text("Thinking...")
            try:
                from agent.core import AgentCore
                from memory.manager import create_memory_manager
                from models.provider import get_provider

                provider = get_provider()
                chat_id = str(update.effective_chat.id)
                memory = create_memory_manager(
                    project_id="default",
                    session_id=f"telegram-{chat_id}",
                    provider=provider,
                )
                agent = AgentCore(
                    provider=provider,
                    memory_manager=memory,
                    project_id="default",
                    session_id=f"telegram-{chat_id}",
                )
                response = await agent.run_autonomous(message)
                # Split long messages
                if len(response) > 4000:
                    for i in range(0, len(response), 4000):
                        await update.message.reply_text(response[i:i+4000])
                else:
                    await update.message.reply_text(response or "No response.")
            except Exception as e:
                await update.message.reply_text(f"Error: {e}")

        async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            if not _is_allowed(update):
                return
            from tasks.scheduler import list_jobs
            jobs = list_jobs()
            status = f"Agent Harness Online\n\nScheduled tasks: {len(jobs)}"
            if jobs:
                for j in jobs[:5]:
                    status += f"\n• {j['name']} (next: {j['next_run'] or 'N/A'})"
            await update.message.reply_text(status)

        async def files_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            if not _is_allowed(update):
                return
            from config import get_settings as gs
            s = gs()
            workspace = s.workspace_dir
            files = list(workspace.glob("**/*"))[:20]
            if not files:
                await update.message.reply_text("No files in workspace.")
                return
            file_list = "\n".join(f"• {f.relative_to(workspace)}" for f in files if f.is_file())
            await update.message.reply_text(f"Workspace files:\n{file_list}")

        async def task_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            if not _is_allowed(update):
                return
            description = " ".join(context.args) if context.args else ""
            if not description:
                await update.message.reply_text("Usage: /task <description>")
                return
            from tasks.scheduler import schedule_agent_task
            task_id = await schedule_agent_task(
                name=description[:50],
                description=description,
                schedule="now",
                project_id="default",
            )
            await update.message.reply_text(f"Task scheduled! ID: {task_id}\n\n{description}")

        async def memory_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            if not _is_allowed(update):
                return
            query = " ".join(context.args) if context.args else ""
            if not query:
                await update.message.reply_text("Usage: /memory <search query>")
                return
            from memory.manager import create_memory_manager
            manager = create_memory_manager(project_id="default")
            results = await manager.recall(query, tiers=["semantic", "episodic"])
            if not results:
                await update.message.reply_text("No relevant memories found.")
                return
            lines = [f"Memory search: '{query}'\n"]
            for r in results[:5]:
                source = r.get("source", "?")
                content = r.get("content", "")[:200]
                lines.append(f"[{source}] {content}")
            await update.message.reply_text("\n\n".join(lines))

        app.add_handler(CommandHandler("start", start_cmd))
        app.add_handler(CommandHandler("chat", chat_cmd))
        app.add_handler(CommandHandler("status", status_cmd))
        app.add_handler(CommandHandler("files", files_cmd))
        app.add_handler(CommandHandler("task", task_cmd))
        app.add_handler(CommandHandler("memory", memory_cmd))

        _application = app
        await app.initialize()
        await app.start()
        # Start polling in background
        asyncio.create_task(app.updater.start_polling(drop_pending_updates=True))
        logger.info("Telegram bot started successfully")

    except ImportError:
        logger.warning("python-telegram-bot not installed, Telegram disabled")
    except Exception as e:
        logger.error(f"Failed to start Telegram bot: {e}")
        raise


def _is_allowed(update: Any) -> bool:
    """Check if the chat ID is in the allowed list."""
    allowed_ids = settings.telegram_allowed_ids
    if not allowed_ids:
        return True  # No restriction if not configured
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id not in allowed_ids:
        logger.warning(f"Unauthorized Telegram access from chat_id: {chat_id}")
        return False
    return True


async def send_message_to_all(message: str) -> None:
    """Send a message to all allowed Telegram chat IDs."""
    if not settings.telegram_bot_token or not settings.telegram_allowed_ids:
        return
    if _application is None:
        logger.debug("Telegram application not initialized, skipping message")
        return
    try:
        for chat_id in settings.telegram_allowed_ids:
            await _application.bot.send_message(
                chat_id=chat_id,
                text=message[:4096],
            )
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")

import logging
import sys


def setup_logging():
    """
    تهيئة نظام تسجيل الأحداث (Logging) للتطبيق بالكامل وبشكل موحد.
    """
    logger = logging.getLogger("smarthunt")

    # منع تكرار الـ handlers إذا تم استدعاء الدالة أكثر من مرة
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    # تنسيق سجل الأحداث
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # الإخراج على الـ Console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info("SmartHunt system logging initialized successfully.")
    return logger

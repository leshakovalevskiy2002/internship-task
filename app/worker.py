from app.config.broker import configure_broker

configure_broker()

import app.tasks.reports

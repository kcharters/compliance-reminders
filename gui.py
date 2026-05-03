"""Streamlit GUI for the Compliance Reminder Scheduler."""

import json
import os
import smtplib
import sys
from datetime import date, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import streamlit as st
from dotenv import dotenv_values, set_key

# Ensure project root is on the path so we can import local modules
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from reminders.definitions import load_reminders, save_reminders  # noqa: E402
from reminders.renderer import render  # noqa: E402

REMINDERS = load_reminders()

# ── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Compliance Reminders",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    /* Sidebar */
    [data-testid="stSidebar"] { background: #111111; }

    /* Metric cards */
    .card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 12px;
    }
    .card-title { font-size: 15px; font-weight: 600; color: #b7afa3; margin-bottom: 4px; }
    .card-sub   { font-size: 12px; color: #6b705c; margin-bottom: 10px; }

    /* Urgency pills */
    .pill-red    { background: #ef444422; color: #ef4444; border: 1px solid #ef444440;
                   border-radius: 999px; padding: 3px 12px; font-size: 12px; font-weight: 600; }
    .pill-amber  { background: #f59e0b22; color: #f59e0b; border: 1px solid #f59e0b40;
                   border-radius: 999px; padding: 3px 12px; font-size: 12px; font-weight: 600; }
    .pill-green  { background: #10b98122; color: #10b981; border: 1px solid #10b98140;
                   border-radius: 999px; padding: 3px 12px; font-size: 12px; font-weight: 600; }
    .pill-grey   { background: #6b705c22; color: #6b705c; border: 1px solid #6b705c40;
                   border-radius: 999px; padding: 3px 12px; font-size: 12px; font-weight: 600; }

    /* Divider */
    hr { border-color: #2a2a2a; margin: 6px 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Helpers ──────────────────────────────────────────────────────────────────

ENV_FILE = ROOT / ".env"


def days_remaining(reminder: dict) -> int:
    return (date.fromisoformat(reminder["deadline"]) - date.today()).days


def urgency_label(days: int) -> str:
    if days < 0:
        return "Overdue"
    if days <= 7:
        return f"{days}d – Critical"
    if days <= 30:
        return f"{days}d – Soon"
    return f"{days}d – OK"


def urgency_pill_class(days: int) -> str:
    if days < 0:
        return "pill-red"
    if days <= 7:
        return "pill-red"
    if days <= 30:
        return "pill-amber"
    return "pill-green"


def urgency_progress(days: int) -> float:
    """Return 0–1 where 1 means most urgent (close/overdue)."""
    if days <= 0:
        return 1.0
    return max(0.0, 1.0 - days / 90)


def next_fire_in(reminder: dict) -> str:
    days = days_remaining(reminder)
    if days < 0:
        return "—"
    thresholds = sorted(reminder["days_before"], reverse=True)
    for t in thresholds:
        if days >= t:
            return f"at {t}d mark (in {days - t}d)"
    return f"next threshold: {thresholds[-1]}d" if thresholds else "—"


def would_fire(reminder: dict, sim_date: date) -> bool:
    deadline = date.fromisoformat(reminder["deadline"])
    dr = (deadline - sim_date).days
    return 0 <= dr and dr in reminder["days_before"]


def render_email_preview(reminder: dict) -> str:
    dr = days_remaining(reminder)
    dl = date.fromisoformat(reminder["deadline"])
    return render(
        reminder["template"],
        {
            "reminder_name": reminder["name"],
            "days_remaining": max(dr, 0),
            "deadline": dl.strftime("%d %B %Y"),
        },
    )


# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🛡️ Compliance Reminders")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "🔍 Dry Run", "📧 Email Preview", "⚙️ Settings", "📋 Manage Reminders"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    overdue_count = sum(1 for r in REMINDERS if days_remaining(r) < 0)
    critical_count = sum(1 for r in REMINDERS if 0 <= days_remaining(r) <= 7)
    total = len(REMINDERS)

    st.metric("Total Reminders", total)
    if overdue_count:
        st.metric("🚨 Overdue", overdue_count)
    if critical_count:
        st.metric("⚠️ Critical (≤7d)", critical_count)

    st.markdown("---")
    st.caption(f"Today: {date.today().strftime('%d %B %Y')}")


# ── Pages ─────────────────────────────────────────────────────────────────────

# ── DASHBOARD ────────────────────────────────────────────────────────────────
if page == "📊 Dashboard":
    st.title("Compliance Dashboard")
    st.caption("Live view of all scheduled compliance reminders.")

    # Top summary metrics
    ok_count = sum(1 for r in REMINDERS if days_remaining(r) > 30)
    soon_count = sum(1 for r in REMINDERS if 7 < days_remaining(r) <= 30)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total", total)
    m2.metric("✅ OK", ok_count)
    m3.metric("🟡 Soon (≤30d)", soon_count)
    m4.metric("🔴 Critical / Overdue", critical_count + overdue_count)

    st.markdown("---")

    # Reminder cards (two per row)
    pairs = [REMINDERS[i : i + 2] for i in range(0, len(REMINDERS), 2)]
    for pair in pairs:
        cols = st.columns(len(pair))
        for col, reminder in zip(cols, pair):
            with col:
                dr = days_remaining(reminder)
                pill = urgency_pill_class(dr)
                label = urgency_label(dr)
                deadline_str = date.fromisoformat(reminder["deadline"]).strftime("%d %b %Y")
                recipients = ", ".join(reminder["recipients"])
                next_fire = next_fire_in(reminder)

                st.markdown(
                    f"""
                    <div class="card">
                      <div class="card-title">{reminder["name"]}</div>
                      <div class="card-sub">Deadline: {deadline_str}</div>
                      <span class="{pill}">{label}</span>
                      <hr/>
                      <div class="card-sub" style="margin-top:10px">
                        <b style="color:#b7afa3">Recipients</b><br>{recipients}
                      </div>
                      <div class="card-sub">
                        <b style="color:#b7afa3">Lead times</b><br>{", ".join(str(d)+"d" for d in sorted(reminder["days_before"]))}
                      </div>
                      <div class="card-sub">
                        <b style="color:#b7afa3">Next email fires</b><br>{next_fire}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                progress = urgency_progress(dr)
                color = "#ef4444" if dr <= 7 else "#f59e0b" if dr <= 30 else "#10b981"
                st.progress(progress, text=f"{max(dr, 0)} days remaining")


# ── DRY RUN ──────────────────────────────────────────────────────────────────
elif page == "🔍 Dry Run":
    st.title("Dry Run")
    st.caption("Simulate which reminders would fire on a given date — no emails sent.")

    sim_date = st.date_input(
        "Simulation date",
        value=date.today(),
        min_value=date.today() - timedelta(days=365),
        max_value=date.today() + timedelta(days=365),
    )

    st.markdown("---")

    any_fires = False
    for reminder in REMINDERS:
        fires = would_fire(reminder, sim_date)
        deadline = date.fromisoformat(reminder["deadline"])
        dr_sim = (deadline - sim_date).days

        icon = "🔔" if fires else "💤"
        status_text = f"**WOULD FIRE** — {dr_sim}d before deadline" if fires else f"No match — {dr_sim}d remaining"
        status_color = "#10b981" if fires else "#6b705c"

        with st.expander(f"{icon} {reminder['name']}", expanded=fires):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(
                    f"<span style='color:{status_color};font-weight:600'>{status_text}</span>",
                    unsafe_allow_html=True,
                )
                st.caption(f"Deadline: {deadline.strftime('%d %B %Y')}  ·  Lead times: {reminder['days_before']}")
                st.caption(f"Recipients: {', '.join(reminder['recipients'])}")
            with c2:
                if fires:
                    st.success("✅ Email queued")
                else:
                    st.info("Skipped")

        if fires:
            any_fires = True

    st.markdown("---")
    if any_fires:
        st.success(f"On **{sim_date.strftime('%d %B %Y')}**, at least one reminder would fire.")
    else:
        st.info(f"On **{sim_date.strftime('%d %B %Y')}**, no reminders would fire.")


# ── EMAIL PREVIEW ────────────────────────────────────────────────────────────
elif page == "📧 Email Preview":
    st.title("Email Preview")
    st.caption("Render the email template for any reminder as it would appear to recipients.")

    reminder_names = [r["name"] for r in REMINDERS]
    choice = st.selectbox("Select reminder", reminder_names)
    reminder = next(r for r in REMINDERS if r["name"] == choice)

    st.markdown(
        f"**Recipients:** {', '.join(reminder['recipients'])}  \n"
        f"**Deadline:** {date.fromisoformat(reminder['deadline']).strftime('%d %B %Y')}  \n"
        f"**Template:** `{reminder['template']}`"
    )

    col_render, col_send = st.columns(2)

    if col_render.button("👁️ Render Email", use_container_width=True):
        try:
            html = render_email_preview(reminder)
            st.markdown("#### Preview")
            st.components.v1.html(html, height=500, scrolling=True)
        except Exception as e:
            st.error(f"Failed to render template: {e}")

    if col_send.button("📤 Send Test Email", use_container_width=True):
        env_live = dotenv_values(ENV_FILE) if ENV_FILE.exists() else {}
        smtp_user = env_live.get("EMAIL_USER", "")
        smtp_pass = env_live.get("EMAIL_PASSWORD", "")
        smtp_host = env_live.get("EMAIL_HOST", "smtp.gmail.com")
        smtp_port = int(env_live.get("EMAIL_PORT", "587"))
        smtp_from = env_live.get("EMAIL_FROM", smtp_user)
        if not smtp_user or not smtp_pass:
            st.warning("⚙️ Configure SMTP credentials in Settings before sending a test email.")
        else:
            try:
                html = render_email_preview(reminder)
                msg = MIMEMultipart("alternative")
                msg["Subject"] = f"[TEST] {reminder['name']}"
                msg["From"] = smtp_from
                msg["To"] = ", ".join(reminder["recipients"])
                msg.attach(MIMEText(html, "html"))
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.ehlo()
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(smtp_from, reminder["recipients"], msg.as_string())
                st.success(f"✅ Test email sent to {', '.join(reminder['recipients'])}")
            except Exception as e:
                st.error(f"Failed to send: {e}")


# ── SETTINGS ─────────────────────────────────────────────────────────────────
elif page == "⚙️ Settings":
    st.title("Settings")
    st.caption("Configure SMTP and application settings. Changes are saved to `.env`.")

    env_vals = dotenv_values(ENV_FILE) if ENV_FILE.exists() else {}

    with st.form("smtp_form"):
        st.subheader("SMTP / Email")
        c1, c2 = st.columns(2)
        host = c1.text_input("SMTP Host", value=env_vals.get("EMAIL_HOST", "smtp.gmail.com"))
        port = c2.text_input("SMTP Port", value=env_vals.get("EMAIL_PORT", "587"))
        user = c1.text_input("Email User / Login", value=env_vals.get("EMAIL_USER", ""))
        password = c2.text_input("Email Password", value=env_vals.get("EMAIL_PASSWORD", ""), type="password")
        from_addr = st.text_input("From Address", value=env_vals.get("EMAIL_FROM", ""))

        st.subheader("Application")
        c3, c4 = st.columns(2)
        timezone = c3.selectbox(
            "Timezone",
            ["UTC", "America/New_York", "America/Chicago", "America/Los_Angeles", "Europe/London", "Europe/Paris", "Asia/Tokyo"],
            index=["UTC", "America/New_York", "America/Chicago", "America/Los_Angeles", "Europe/London", "Europe/Paris", "Asia/Tokyo"].index(
                env_vals.get("TIMEZONE", "UTC")
            )
            if env_vals.get("TIMEZONE", "UTC")
            in ["UTC", "America/New_York", "America/Chicago", "America/Los_Angeles", "Europe/London", "Europe/Paris", "Asia/Tokyo"]
            else 0,
        )
        log_level = c4.selectbox(
            "Log Level",
            ["DEBUG", "INFO", "WARNING", "ERROR"],
            index=["DEBUG", "INFO", "WARNING", "ERROR"].index(env_vals.get("LOG_LEVEL", "INFO")),
        )

        submitted = st.form_submit_button("💾 Save Settings", type="primary")

    if submitted:
        if not ENV_FILE.exists():
            ENV_FILE.touch()
        set_key(str(ENV_FILE), "EMAIL_HOST", host)
        set_key(str(ENV_FILE), "EMAIL_PORT", port)
        set_key(str(ENV_FILE), "EMAIL_USER", user)
        set_key(str(ENV_FILE), "EMAIL_PASSWORD", password)
        set_key(str(ENV_FILE), "EMAIL_FROM", from_addr or user)
        set_key(str(ENV_FILE), "TIMEZONE", timezone)
        set_key(str(ENV_FILE), "LOG_LEVEL", log_level)
        st.success("✅ Settings saved to .env")

    st.markdown("---")
    st.subheader("Reminder Definitions")
    st.caption("Reminders are defined in `reminders/definitions.py`. Current reminders:")
    for r in REMINDERS:
        with st.expander(r["name"]):
            st.json(
                {
                    "id": r["id"],
                    "deadline": r["deadline"],
                    "days_before": r["days_before"],
                    "schedule": r["schedule"],
                    "recipients": r["recipients"],
                    "template": r["template"],
                }
            )


# ── MANAGE REMINDERS ─────────────────────────────────────────────────────────
elif page == "📋 Manage Reminders":
    st.title("Manage Reminders")
    st.caption("Add or remove compliance reminders. Changes are saved immediately to `reminders/reminders.json`.")

    _TEMPLATES = sorted(p.name for p in (ROOT / "templates").glob("*.html"))

    st.markdown("---")
    st.subheader("Current Reminders")

    header_cols = st.columns([3, 2, 2, 1])
    header_cols[0].markdown("**Name**")
    header_cols[1].markdown("**Deadline**")
    header_cols[2].markdown("**Status**")
    header_cols[3].markdown("**Action**")
    st.divider()

    for r in REMINDERS:
        dr = days_remaining(r)
        pill = urgency_pill_class(dr)
        label = urgency_label(dr)
        deadline_str = date.fromisoformat(r["deadline"]).strftime("%d %b %Y")
        row = st.columns([3, 2, 2, 1])
        row[0].markdown(f"**{r['name']}**  \n`{r['id']}`")
        row[1].markdown(deadline_str)
        row[2].markdown(f"<span class='{pill}'>{label}</span>", unsafe_allow_html=True)
        if row[3].button("🗑️", key=f"del_{r['id']}", help=f"Delete {r['name']}"):
            updated = [x for x in REMINDERS if x["id"] != r["id"]]
            save_reminders(updated)
            st.success(f"Deleted **{r['name']}**")
            st.rerun()
        st.divider()

    st.markdown("---")
    st.subheader("Add New Reminder")

    with st.form("add_reminder_form"):
        c1, c2 = st.columns(2)
        new_name = c1.text_input("Name", placeholder="e.g. HIPAA Risk Assessment")
        new_deadline = c2.date_input("Deadline", value=date.today() + timedelta(days=30))

        c3, c4 = st.columns(2)
        new_recipients = c3.text_area("Recipients (one per line)", placeholder="compliance@example.com\naudit@example.com")
        new_days_before = c4.text_input("Lead times – days before deadline (comma-separated)", value="30, 14, 7, 1")

        c5, c6, c7 = st.columns(3)
        new_template = c5.selectbox("Email Template", _TEMPLATES)
        new_hour = c6.number_input("Schedule Hour (0–23)", min_value=0, max_value=23, value=8)
        new_minute = c7.number_input("Schedule Minute (0–59)", min_value=0, max_value=59, value=0)

        submitted = st.form_submit_button("➕ Add Reminder", type="primary")

    if submitted:
        if not new_name.strip() or not new_recipients.strip():
            st.error("Name and at least one recipient are required.")
        else:
            try:
                days = [int(d.strip()) for d in new_days_before.split(",") if d.strip()]
                if not days:
                    raise ValueError("At least one lead time is required.")
                recipients = [addr.strip() for addr in new_recipients.strip().splitlines() if addr.strip()]
                new_id = new_name.strip().lower().replace(" ", "_").replace("-", "_")
                existing_ids = {r["id"] for r in REMINDERS}
                base_id, n = new_id, 2
                while new_id in existing_ids:
                    new_id = f"{base_id}_{n}"
                    n += 1
                new_reminder = {
                    "id": new_id,
                    "name": new_name.strip(),
                    "recipients": recipients,
                    "schedule": {"hour": int(new_hour), "minute": int(new_minute)},
                    "days_before": sorted(days, reverse=True),
                    "deadline": new_deadline.isoformat(),
                    "template": new_template,
                }
                save_reminders(REMINDERS + [new_reminder])
                st.success(f"✅ Added **{new_name.strip()}**")
                st.rerun()
            except ValueError as e:
                st.error(f"Invalid input: {e}")

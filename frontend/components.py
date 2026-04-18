"""Shared UI helpers for the Streamlit frontend."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from html import escape
from typing import Any, Sequence

import pandas as pd
import streamlit as st


APP_TITLE = "Recruitment Management System"
APP_SUBTITLE = "Role-based recruitment workflows for employers and candidates."


def apply_base_styles() -> None:
    """Apply the light dashboard design system based on the reference shell."""

    st.markdown(
        """
        <style>
            @import url("https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap");
            @import url("https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:FILL@0;wght@400;GRAD@0;opsz@24");
            @import url("https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:FILL@0;wght@400;GRAD@0;opsz@24");

            :root {
                --primary: #0C5CAB;
                --primary-strong: #0a4a8a;
                --success: #10b981;
                --warning: #f59e0b;
                --danger: #ef4444;
                --info: #3b82f6;
                --canvas: #f6f8fb;
                --surface: #ffffff;
                --surface-subtle: #f9fafb;
                --border: #e5e7eb;
                --border-strong: #d1d5db;
                --text: #111827;
                --text-soft: #6b7280;
                --text-muted: #9ca3af;
                --shadow-sm: 0 1px 2px rgba(16, 24, 40, 0.05);
                --shadow-md: 0 8px 24px rgba(16, 24, 40, 0.06);
                --shadow-lg: 0 18px 42px rgba(16, 24, 40, 0.08);
                --radius-lg: 16px;
                --radius-md: 12px;
                --radius-sm: 10px;
            }

            html, body, [class*="css"], [data-testid="stAppViewContainer"] * {
                font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
            }

            .material-symbols-outlined,
            .material-symbols-rounded,
            [class*="material-symbols"] {
                font-family: "Material Symbols Rounded", "Material Symbols Outlined" !important;
                font-weight: normal;
                font-style: normal;
                font-size: 20px;
                line-height: 1;
                letter-spacing: normal;
                text-transform: none;
                display: inline-block;
                white-space: nowrap;
                word-wrap: normal;
                direction: ltr;
                -webkit-font-smoothing: antialiased;
            }

            .stApp {
                background:
                    radial-gradient(circle at 12% 8%, rgba(12, 92, 171, 0.03), transparent 24%),
                    radial-gradient(circle at 86% 10%, rgba(59, 130, 246, 0.03), transparent 20%),
                    linear-gradient(180deg, #f8fafc 0%, #f6f8fb 100%);
                color: var(--text);
            }

            [data-testid="stAppViewContainer"] {
                background: transparent;
            }

            [data-testid="stHeader"] {
                background: transparent;
                border-bottom: none;
            }

            [data-testid="stToolbar"] {
                right: 0.5rem;
            }

            [data-testid="collapsedControl"] {
                display: none;
            }

            h1, h2, h3, h4, h5, h6, label, p, span, div, li {
                color: var(--text);
            }

            a {
                color: var(--primary);
            }

            section[data-testid="stSidebarNav"] {
                display: none;
            }

            [data-testid="stSidebar"] {
                display: none;
            }

            .sidebar-shell {
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                padding: 0.95rem;
                background: var(--surface);
                box-shadow: var(--shadow-md);
                margin-bottom: 1rem;
            }

            .sidebar-eyebrow {
                letter-spacing: 0.14em;
                text-transform: uppercase;
                color: var(--text-muted);
                font-size: 0.72rem;
                font-weight: 600;
                margin-bottom: 0.55rem;
            }

            .sidebar-title {
                font-size: 1.08rem;
                font-weight: 600;
                color: var(--text);
                margin-bottom: 0.25rem;
            }

            .sidebar-copy {
                color: var(--text-soft);
                font-size: 0.88rem;
                line-height: 1.45;
                margin-bottom: 0.28rem;
            }

            .sidebar-chip {
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
                margin-top: 0.55rem;
                padding: 0.3rem 0.68rem;
                border-radius: 999px;
                background: rgba(12, 92, 171, 0.08);
                border: 1px solid rgba(12, 92, 171, 0.16);
                color: var(--primary);
                font-size: 0.76rem;
                font-weight: 600;
            }

            .sidebar-nav-title {
                margin: 0.95rem 0 0.58rem 0;
                color: var(--text-muted);
                text-transform: uppercase;
                letter-spacing: 0.12em;
                font-size: 0.72rem;
                font-weight: 600;
            }

            .topbar-shell {
                border: 1px solid var(--border);
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.92);
                box-shadow: var(--shadow-sm);
                padding: 0.68rem 0.9rem;
                margin-bottom: 1rem;
            }

            .topbar-brand {
                display: flex;
                align-items: center;
                gap: 0.7rem;
            }

            .topbar-mark {
                width: 28px;
                height: 28px;
                border-radius: 8px;
                background: linear-gradient(180deg, var(--primary), var(--primary-strong));
                color: white;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 0.86rem;
                font-weight: 700;
                box-shadow: 0 8px 20px rgba(12, 92, 171, 0.18);
            }

            .topbar-title {
                font-size: 1.08rem;
                font-weight: 600;
                line-height: 1.1;
            }

            .topbar-title span {
                color: var(--primary);
            }

            .topbar-breadcrumb {
                display: flex;
                align-items: center;
                gap: 0.48rem;
                font-size: 0.88rem;
                color: var(--text-soft);
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .topbar-breadcrumb strong {
                color: var(--text);
                font-weight: 600;
            }

            .topbar-search {
                display: flex;
                align-items: center;
                gap: 0.55rem;
                min-height: 40px;
                border: 1px solid var(--border);
                border-radius: 12px;
                background: var(--surface-subtle);
                color: var(--text-muted);
                padding: 0 0.9rem;
                font-size: 0.88rem;
            }

            .topbar-key {
                margin-left: auto;
                border: 1px solid var(--border);
                border-radius: 8px;
                background: white;
                color: var(--text-soft);
                padding: 0.08rem 0.38rem;
                font-size: 0.74rem;
                font-weight: 600;
            }

            .topbar-avatar {
                width: 34px;
                height: 34px;
                border-radius: 999px;
                background: linear-gradient(180deg, #4f9ce6, #2d76c4);
                color: white;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 0.8rem;
                font-weight: 700;
                box-shadow: 0 10px 20px rgba(37, 99, 235, 0.16);
            }

            .topbar-icon {
                width: 34px;
                height: 34px;
                border-radius: 999px;
                border: 1px solid var(--border);
                background: white;
                color: var(--text-soft);
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 0.84rem;
            }

            .hero-card {
                margin-bottom: 1rem;
            }

            .resource-card {
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                background: var(--surface);
                box-shadow: var(--shadow-sm);
                padding: 1rem;
                min-height: 128px;
            }

            .resource-top {
                display: flex;
                align-items: flex-start;
                gap: 0.75rem;
                margin-bottom: 0.7rem;
            }

            .resource-icon {
                width: 30px;
                height: 30px;
                border-radius: 10px;
                border: 1px solid var(--border);
                background: var(--surface-subtle);
                display: inline-flex;
                align-items: center;
                justify-content: center;
                color: var(--text-soft);
                font-size: 0.82rem;
                flex-shrink: 0;
            }

            .resource-title {
                color: var(--text);
                font-size: 0.95rem;
                font-weight: 600;
                line-height: 1.25;
            }

            .resource-subtitle {
                color: var(--text-soft);
                font-size: 0.82rem;
                line-height: 1.3;
                margin-top: 0.08rem;
            }

            .resource-meta {
                color: var(--text-soft);
                font-size: 0.82rem;
                line-height: 1.35;
                margin-bottom: 0.85rem;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .resource-footer {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 0.75rem;
            }

            .resource-time {
                color: var(--text-muted);
                font-size: 0.78rem;
                white-space: nowrap;
            }

            .status-badge {
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
                padding: 0.24rem 0.58rem;
                border-radius: 999px;
                font-size: 0.74rem;
                font-weight: 500;
                line-height: 1;
                border: 1px solid transparent;
                white-space: nowrap;
            }

            .status-badge.success {
                color: #166534;
                background: #ecfdf3;
                border-color: #bbf7d0;
            }

            .status-badge.warning {
                color: #9a6700;
                background: #fffbeb;
                border-color: #fde68a;
            }

            .status-badge.danger {
                color: #b42318;
                background: #fef3f2;
                border-color: #fecaca;
            }

            .status-badge.info {
                color: var(--primary);
                background: #eff6ff;
                border-color: #bfdbfe;
            }

            .status-badge.neutral {
                color: #475467;
                background: #f8fafc;
                border-color: #e2e8f0;
            }

            .quiet-table-wrap {
                overflow-x: auto;
                border: 1px solid var(--border);
                border-radius: var(--radius-md);
                background: var(--surface);
                box-shadow: var(--shadow-sm);
            }

            .quiet-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 0.88rem;
            }

            .quiet-table thead th {
                background: #fcfcfd;
                color: var(--text-muted);
                text-align: left;
                font-size: 0.76rem;
                font-weight: 600;
                padding: 0.85rem 1rem;
                border-bottom: 1px solid var(--border);
                white-space: nowrap;
            }

            .quiet-table tbody td {
                color: var(--text);
                padding: 0.85rem 1rem;
                border-bottom: 1px solid #eef2f7;
                vertical-align: top;
            }

            .quiet-table tbody tr:hover {
                background: #fafcff;
            }

            .quiet-table tbody tr:last-child td {
                border-bottom: none;
            }

            .activity-table-wrap {
                border: 1px solid var(--border);
                border-radius: var(--radius-md);
                background: var(--surface);
                box-shadow: var(--shadow-sm);
                overflow: hidden;
            }

            .activity-grid {
                display: block;
                width: 100%;
                font-size: 0.88rem;
            }

            .activity-grid-header,
            .activity-grid-row {
                display: grid;
                grid-template-columns: minmax(320px, 3.2fr) minmax(120px, 1fr) minmax(150px, 1.1fr) minmax(110px, 0.8fr);
                gap: 0;
                align-items: stretch;
            }

            .activity-grid-header {
                background: #fcfcfd;
                border-bottom: 1px solid var(--border);
            }

            .activity-grid-head {
                color: var(--text-soft);
                text-align: left;
                font-size: 0.76rem;
                font-weight: 600;
                padding: 0.85rem 1rem;
                white-space: nowrap;
            }

            .activity-grid-head.time,
            .activity-grid-cell.time {
                text-align: right;
            }

            .activity-grid-row {
                border-bottom: 1px solid #eef2f7;
            }

            .activity-grid-row:last-child {
                border-bottom: none;
            }

            .activity-grid-row:hover {
                background: #fafcff;
            }

            .activity-grid-cell {
                padding: 0.95rem 1rem;
                vertical-align: middle;
            }

            .activity-commit {
                display: flex;
                align-items: flex-start;
                gap: 0.8rem;
            }

            .activity-avatar {
                width: 26px;
                height: 26px;
                border-radius: 999px;
                background: #e5e7eb;
                color: #374151;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 0.72rem;
                font-weight: 600;
                flex-shrink: 0;
                margin-top: 0.05rem;
            }

            .activity-title {
                color: var(--text);
                font-size: 0.95rem;
                font-weight: 600;
                line-height: 1.3;
                margin-bottom: 0.15rem;
            }

            .activity-subtitle {
                color: var(--text-soft);
                font-size: 0.82rem;
                line-height: 1.35;
            }

            .activity-detail {
                color: var(--text-muted);
                font-size: 0.78rem;
                line-height: 1.4;
                margin-top: 0.18rem;
            }

            .branch-chip {
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
                padding: 0.24rem 0.58rem;
                border-radius: 8px;
                background: #f8fafc;
                border: 1px solid var(--border);
                color: var(--text-soft);
                font-size: 0.78rem;
                line-height: 1;
                white-space: nowrap;
            }

            .time-cell {
                color: var(--text-soft);
                font-size: 0.84rem;
                white-space: nowrap;
                text-align: right;
            }

            @media (max-width: 1100px) {
                .activity-grid-header,
                .activity-grid-row {
                    grid-template-columns: minmax(260px, 2.4fr) minmax(110px, 0.9fr) minmax(130px, 1fr) minmax(90px, 0.7fr);
                }
            }

            @media (max-width: 860px) {
                .activity-grid-header {
                    display: none;
                }

                .activity-grid-row {
                    grid-template-columns: 1fr;
                    gap: 0;
                    padding: 0.3rem 0;
                }

                .activity-grid-cell {
                    padding: 0.35rem 1rem;
                }

                .activity-grid-cell.status::before,
                .activity-grid-cell.branch::before,
                .activity-grid-cell.time::before {
                    display: block;
                    color: var(--text-muted);
                    font-size: 0.72rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.08em;
                    margin-bottom: 0.28rem;
                }

                .activity-grid-cell.status::before {
                    content: "Status";
                }

                .activity-grid-cell.branch::before {
                    content: "Reference";
                }

                .activity-grid-cell.time::before {
                    content: "Time";
                }

                .activity-grid-cell.time {
                    text-align: left;
                }
            }

            .table-empty {
                border: 1px dashed var(--border-strong);
                border-radius: var(--radius-md);
                padding: 1rem;
                background: white;
                color: var(--text-soft);
            }

            .table-caption {
                color: var(--text-muted);
                font-size: 0.8rem;
                margin-bottom: 0.55rem;
            }

            .cell-muted {
                color: var(--text-soft);
            }

            .log-panel {
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                background: var(--surface);
                box-shadow: var(--shadow-sm);
                overflow: hidden;
            }

            .log-body {
                max-height: 320px;
                overflow: auto;
                padding: 0.9rem 1rem;
                background: #fbfcfe;
                border-top: 1px solid var(--border);
                font-family: "IBM Plex Sans", monospace;
                font-size: 0.82rem;
                line-height: 1.55;
                color: #374151;
            }

            .log-line {
                margin-bottom: 0.28rem;
            }

            .hero-eyebrow {
                letter-spacing: 0.12em;
                text-transform: uppercase;
                color: var(--text-muted);
                font-size: 0.72rem;
                font-weight: 600;
            }
            .hero-title {
                color: var(--text);
                margin: 0.35rem 0 0.24rem 0;
                font-size: clamp(1.75rem, 2vw, 2.15rem);
                line-height: 1.08;
                font-weight: 600;
            }
            .hero-copy {
                color: var(--text-soft);
                margin: 0;
                font-size: 0.92rem;
                max-width: 68ch;
                line-height: 1.5;
            }
            .info-chip {
                border: 1px solid var(--border);
                border-radius: var(--radius-md);
                padding: 1rem;
                background: var(--surface);
                min-height: 132px;
                box-shadow: var(--shadow-sm);
            }
            .info-chip h4 {
                margin: 0 0 0.4rem 0;
                color: var(--text);
                font-size: 1rem;
                font-weight: 600;
            }
            .info-chip p {
                margin: 0.16rem 0;
                color: var(--text-soft);
                line-height: 1.45;
                font-size: 0.92rem;
            }

            .panel-head {
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                gap: 1rem;
                margin-bottom: 0.9rem;
            }

            .panel-copy {
                flex: 1;
                min-width: 0;
            }

            .panel-eyebrow {
                color: var(--text-muted);
                text-transform: uppercase;
                letter-spacing: 0.12em;
                font-size: 0.7rem;
                font-weight: 600;
                margin-bottom: 0.35rem;
            }

            .panel-title {
                color: var(--text);
                font-size: 1.08rem;
                font-weight: 600;
                line-height: 1.2;
                margin-bottom: 0.2rem;
            }

            .panel-subtitle {
                color: var(--text-soft);
                font-size: 0.9rem;
                line-height: 1.45;
            }

            .panel-badge {
                display: inline-flex;
                align-items: center;
                min-height: 30px;
                padding: 0.24rem 0.68rem;
                border-radius: 999px;
                font-size: 0.74rem;
                font-weight: 600;
                border: 1px solid var(--border);
                background: var(--surface-subtle);
                color: var(--text-soft);
                white-space: nowrap;
            }

            .metric-card {
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                padding: 1rem;
                background: var(--surface);
                box-shadow: var(--shadow-sm);
                min-height: 104px;
            }

            .metric-label {
                color: var(--text-muted);
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 600;
                margin-bottom: 0.75rem;
            }

            .metric-value {
                color: var(--text);
                font-size: clamp(1.35rem, 1.8vw, 1.9rem);
                line-height: 1.05;
                font-weight: 600;
            }

            .metric-helper {
                color: var(--text-soft);
                font-size: 0.86rem;
                margin-top: 0.4rem;
            }

            div[data-testid="stVerticalBlockBorderWrapper"],
            div[data-testid="stForm"] {
                border: 1px solid var(--border) !important;
                border-radius: var(--radius-lg) !important;
                background: rgba(255, 255, 255, 0.98);
                box-shadow: var(--shadow-sm);
            }

            div[data-testid="stForm"] {
                padding: 0.2rem 0.2rem 0.4rem 0.2rem;
            }

            div[data-testid="stDataFrame"] {
                border: 1px solid var(--border) !important;
                border-radius: var(--radius-md) !important;
                overflow: hidden;
                box-shadow: var(--shadow-sm);
                background: white;
            }

            [data-testid="stMetric"] {
                border: 1px solid var(--border);
                border-radius: var(--radius-md);
                padding: 1rem 1rem 0.95rem 1rem;
                background:
                    linear-gradient(180deg, rgba(18, 24, 36, 0.92), rgba(11, 15, 24, 0.78));
                box-shadow: var(--shadow);
            }

            [data-testid="stMetricLabel"] {
                color: var(--text-muted);
            }

            [data-testid="stMetricValue"] {
                color: var(--text);
            }

            div[data-baseweb="input"] > div,
            div[data-baseweb="select"] > div,
            textarea,
            input {
                background: white !important;
                color: var(--text) !important;
                border-radius: 12px !important;
                border: 1px solid var(--border) !important;
            }

            div[data-baseweb="input"] input,
            div[data-baseweb="select"] input,
            div[data-baseweb="select"] span,
            textarea,
            input {
                color: var(--text) !important;
            }

            input::placeholder,
            textarea::placeholder {
                color: var(--text-muted) !important;
            }

            input:focus,
            textarea:focus,
            div[data-baseweb="input"] > div:focus-within,
            div[data-baseweb="select"] > div:focus-within,
            button:focus-visible {
                outline: none !important;
                border-color: rgba(12, 92, 171, 0.52) !important;
                box-shadow: 0 0 0 3px rgba(12, 92, 171, 0.14) !important;
            }

            .stButton > button,
            .stDownloadButton > button,
            [data-testid="baseButton-secondary"] {
                background: white !important;
                color: var(--text) !important;
                border: 1px solid var(--border) !important;
                border-radius: 12px !important;
                min-height: 40px !important;
                font-weight: 600 !important;
                box-shadow: var(--shadow-sm);
            }

            .stButton > button:hover,
            .stDownloadButton > button:hover {
                background: #f9fafb !important;
                border-color: var(--border-strong) !important;
            }

            .stTabs [data-baseweb="tab-list"] {
                gap: 0.3rem;
                background: transparent;
                padding: 0;
                border-bottom: 1px solid var(--border);
            }

            .stTabs [data-baseweb="tab"] {
                height: 40px;
                padding: 0 0.55rem;
                border-radius: 10px 10px 0 0;
                background: transparent;
                color: var(--text-muted);
            }

            .stTabs [aria-selected="true"] {
                background: #ffffff !important;
                color: var(--text) !important;
                box-shadow: inset 0 -2px 0 var(--primary);
            }

            [data-testid="stExpander"] details {
                border: 1px solid var(--border);
                border-radius: var(--radius-md);
                background: var(--surface);
                box-shadow: var(--shadow-sm);
            }

            [data-testid="stExpander"] summary {
                color: var(--text);
                display: flex;
                align-items: center;
                gap: 0.55rem;
                min-height: 46px;
                padding: 0.15rem 0.2rem;
                line-height: 1.35;
            }

            [data-testid="stExpander"] summary p,
            [data-testid="stExpander"] summary span {
                margin: 0;
                line-height: 1.35;
            }

            [data-testid="stExpander"] summary svg {
                flex-shrink: 0;
            }

            .profile-expander {
                border: 1px solid var(--border);
                border-radius: var(--radius-md);
                background: var(--surface);
                box-shadow: var(--shadow-sm);
                margin-bottom: 0.75rem;
                overflow: hidden;
            }

            .profile-expander summary {
                list-style: none;
                cursor: pointer;
                padding: 0.95rem 1rem;
                display: flex;
                align-items: center;
                gap: 0.75rem;
                color: var(--text);
                font-size: 0.95rem;
                font-weight: 600;
            }

            .profile-expander summary::-webkit-details-marker {
                display: none;
            }

            .profile-expander summary::before {
                content: "▸";
                color: var(--text-soft);
                font-size: 0.95rem;
                flex-shrink: 0;
                transition: transform 0.15s ease;
            }

            .profile-expander[open] summary::before {
                transform: rotate(90deg);
            }

            .profile-expander summary:hover {
                background: #fafcff;
            }

            .profile-expander-body {
                border-top: 1px solid var(--border);
                padding: 1rem;
                background: #fcfdff;
            }

            .profile-expander-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 1rem 1.5rem;
            }

            .profile-expander-section h4 {
                margin: 0 0 0.75rem 0;
                font-size: 0.95rem;
                font-weight: 600;
                color: var(--text);
            }

            .profile-expander-line {
                margin: 0 0 0.45rem 0;
                color: var(--text-soft);
                font-size: 0.9rem;
                line-height: 1.45;
            }

            .profile-expander-line strong {
                color: var(--text);
                font-weight: 600;
            }

            @media (max-width: 860px) {
                .profile-expander-grid {
                    grid-template-columns: 1fr;
                }
            }

            [data-testid="stRadio"] label p {
                color: var(--text-soft) !important;
                font-size: 0.92rem !important;
                font-weight: 500 !important;
            }

            [data-testid="stRadio"] label:has(input:checked) {
                border-color: #dbeafe;
                background: #eef4fb;
                box-shadow: inset 0 0 0 1px rgba(12, 92, 171, 0.06);
            }

            div[data-testid="stAlert"] {
                border-radius: 14px;
                border: 1px solid var(--border);
                background: white;
                color: var(--text);
            }

            div.row-widget.stRadio > div {
                gap: 0.3rem;
            }

            div.row-widget.stRadio label {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 12px;
                padding: 0.42rem 0.62rem;
            }

            [data-testid="stCaptionContainer"],
            .stCaption {
                color: var(--text-muted) !important;
            }

            hr {
                border-color: var(--border);
            }

            @media (prefers-reduced-motion: reduce) {
                * {
                    animation: none !important;
                    transition: none !important;
                    scroll-behavior: auto !important;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str, eyebrow: str | None = None) -> None:
    """Render a compact page header."""

    eyebrow_html = f"<div class='hero-eyebrow'>{escape(eyebrow)}</div>" if eyebrow else ""
    st.markdown(
        f"""
        <div class="hero-card">
            {eyebrow_html}
            <div class="hero-title">{escape(title)}</div>
            <p class="hero-copy">{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_chip(title: str, lines: Sequence[str]) -> None:
    """Render a compact information block useful for sample account hints and summaries."""

    body = "".join(f"<p>{escape(line)}</p>" for line in lines)
    st.markdown(
        f"""
        <div class="info-chip">
            <h4>{escape(title)}</h4>
            {body}
        </div>
        """,
        unsafe_allow_html=True,
    )


def panel_header(title: str, subtitle: str | None = None, *, eyebrow: str | None = None, badge: str | None = None) -> None:
    """Render a compact panel heading that matches the dashboard design language."""

    eyebrow_html = f"<div class='panel-eyebrow'>{escape(eyebrow)}</div>" if eyebrow else ""
    subtitle_html = f"<div class='panel-subtitle'>{escape(subtitle)}</div>" if subtitle else ""
    badge_html = f"<div class='panel-badge'>{escape(badge)}</div>" if badge else ""
    st.markdown(
        f"""
        <div class="panel-head">
            <div class="panel-copy">
                {eyebrow_html}
                <div class="panel-title">{escape(title)}</div>
                {subtitle_html}
            </div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_identity_card(display_name: str, role: str, email: str) -> None:
    """Render the authenticated user summary in the dashboard sidebar."""

    st.markdown(
        f"""
        <div class="sidebar-shell">
            <div class="sidebar-eyebrow">{escape(APP_TITLE)}</div>
            <div class="sidebar-title">{escape(display_name)}</div>
            <div class="sidebar-copy">{escape(role)}</div>
            <div class="sidebar-copy">{escape(email)}</div>
            <div class="sidebar-chip">Workspace Active</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_nav_heading(title: str, subtitle: str | None = None) -> None:
    """Render a consistent sidebar navigation heading."""

    subtitle_html = f"<div class='sidebar-copy'>{escape(subtitle)}</div>" if subtitle else ""
    st.markdown(
        f"""
        <div class="sidebar-nav-title">{escape(title)}</div>
        {subtitle_html}
        """,
        unsafe_allow_html=True,
    )


def render_topbar(display_name: str, role: str) -> bool:
    """Render the compact top bar and return whether logout was requested."""

    initials = "".join(part[:1].upper() for part in display_name.split()[:2]) or "RM"
    brand_col, crumb_col, avatar_col, logout_col = st.columns(
        [1.55, 3.05, 0.45, 0.75],
        gap="small",
    )

    with brand_col:
        st.markdown(
            """
            <div class="topbar-shell">
                <div class="topbar-brand">
                    <div class="topbar-mark">&#9672;</div>
                    <div class="topbar-title">Recruitment<span>System</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with crumb_col:
        st.markdown(
            f"""
            <div class="topbar-shell">
                <div class="topbar-breadcrumb">
                    <span>{escape(display_name.lower())}</span>
                    <span>/</span>
                    <strong>{escape(role.lower())}-workspace</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with avatar_col:
        st.markdown(
            f"""
            <div class="topbar-shell" style="text-align:center;">
                <div class="topbar-avatar">{escape(initials[:2])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with logout_col:
        st.markdown("<div style='height:0.16rem'></div>", unsafe_allow_html=True)
        return st.button("Logout", use_container_width=True)


def _serialize_value(value: Any) -> Any:
    """Convert backend values to DataFrame-friendly display values."""

    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    return value


def records_frame(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Convert record lists into a DataFrame for consistent table rendering."""

    if not records:
        return pd.DataFrame()
    normalized = [{key: _serialize_value(value) for key, value in row.items()} for row in records]
    return pd.DataFrame(normalized)


def _status_tone(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"running", "ready", "accepted", "pass", "open", "success"}:
        return "success"
    if normalized in {"building", "deploying", "pending", "reviewed", "interviewing"}:
        return "warning"
    if normalized in {"failed", "fail", "rejected", "error"}:
        return "danger"
    if normalized in {"closed"}:
        return "neutral"
    return "info" if normalized else "neutral"


def status_badge(label: str) -> str:
    """Return HTML for one quiet status badge."""

    tone = _status_tone(label)
    return f"<span class='status-badge {tone}'>{escape(label)}</span>"


def _render_table_cell(column: str, value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "<span class='cell-muted'>-</span>"

    text = str(value)
    if any(token in column.lower() for token in ("status", "result")):
        return status_badge(text)
    return escape(text)


def show_records(records: list[dict[str, Any]], empty_message: str, *, height: int = 360) -> None:
    """Render quiet HTML tables instead of default Streamlit grids."""

    if not records:
        st.markdown(f"<div class='table-empty'>{escape(empty_message)}</div>", unsafe_allow_html=True)
        return

    frame = records_frame(records)
    st.markdown(f"<div class='table-caption'>{len(frame)} record(s)</div>", unsafe_allow_html=True)
    headers = "".join(f"<th>{escape(str(column))}</th>" for column in frame.columns)
    rows = []
    for _, row in frame.iterrows():
        cell_html = "".join(
            f"<td>{_render_table_cell(str(column), row[column])}</td>"
            for column in frame.columns
        )
        rows.append(f"<tr>{cell_html}</tr>")

    st.markdown(
        "<div class='quiet-table-wrap' style='max-height:"
        f"{max(height, 180)}px; overflow:auto;'>"
        "<table class='quiet-table'>"
        f"<thead><tr>{headers}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>",
        unsafe_allow_html=True,
    )


def show_activity_table(
    records: list[dict[str, Any]],
    empty_message: str,
    *,
    headers: Sequence[str] | None = None,
) -> None:
    """Render a deployment-style activity table like the reference dashboard."""

    if not records:
        st.markdown(f"<div class='table-empty'>{escape(empty_message)}</div>", unsafe_allow_html=True)
        return

    header_labels = list(headers or ["Commit", "Status", "Branch", "Time"])
    normalized_headers = (header_labels + ["Commit", "Status", "Branch", "Time"])[:4]
    rows: list[str] = []
    for row in records:
        title = str(row.get("title") or row.get("Title") or "-")
        subtitle = str(row.get("subtitle") or row.get("Subtitle") or "")
        status = str(row.get("status") or row.get("Status") or "Unknown")
        branch = str(row.get("branch") or row.get("Branch") or "-")
        time_label = str(row.get("time") or row.get("Time") or "-")
        details = row.get("details") or []
        avatar = escape(title[:1].upper() if title else "?")
        detail_html = "".join(
            f"<div class='activity-detail'>{escape(str(detail))}</div>"
            for detail in details
            if str(detail).strip()
        )
        row_html = f"""
        <div class="activity-grid-row">
            <div class="activity-grid-cell commit">
                <div class="activity-commit">
                    <div class="activity-avatar">{avatar}</div>
                    <div>
                        <div class="activity-title">{escape(title)}</div>
                        <div class="activity-subtitle">{escape(subtitle)}</div>
                        {detail_html}
                    </div>
                </div>
            </div>
            <div class="activity-grid-cell status">{status_badge(status)}</div>
            <div class="activity-grid-cell branch"><span class="branch-chip">&#9679; {escape(branch)}</span></div>
            <div class="activity-grid-cell time"><span class="time-cell">{escape(time_label)}</span></div>
        </div>
        """
        rows.append(row_html)

    st.markdown(
        f"""
        <div class="activity-table-wrap">
            <div class="activity-grid">
                <div class="activity-grid-header">
                    <div class="activity-grid-head">{escape(str(normalized_headers[0]))}</div>
                    <div class="activity-grid-head">{escape(str(normalized_headers[1]))}</div>
                    <div class="activity-grid-head">{escape(str(normalized_headers[2]))}</div>
                    <div class="activity-grid-head time">{escape(str(normalized_headers[3]))}</div>
                </div>
                {''.join(rows)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_reference_activity_table(
    records: list[dict[str, Any]],
    empty_message: str,
    *,
    headers: Sequence[str] | None = None,
) -> None:
    """Render the dashboard activity list using Streamlit columns for stable layout."""

    if not records:
        st.markdown(f"<div class='table-empty'>{escape(empty_message)}</div>", unsafe_allow_html=True)
        return

    header_labels = list(headers or ["Commit", "Status", "Branch", "Time"])
    normalized_headers = (header_labels + ["Commit", "Status", "Branch", "Time"])[:4]
    with st.container(border=True):
        header_cols = st.columns([4.1, 1.5, 2.1, 1.0], gap="small")
        for column, label, align_right in zip(header_cols, normalized_headers, [False, False, False, True]):
            with column:
                alignment = "right" if align_right else "left"
                st.markdown(
                    f"<div class='table-caption' style='margin-bottom:0; text-align:{alignment};'>{escape(str(label))}</div>",
                    unsafe_allow_html=True,
                )
        st.divider()

        for index, row in enumerate(records):
            title = str(row.get("title") or row.get("Title") or "-")
            subtitle = str(row.get("subtitle") or row.get("Subtitle") or "")
            status = str(row.get("status") or row.get("Status") or "Unknown")
            branch = str(row.get("branch") or row.get("Branch") or "-")
            time_label = str(row.get("time") or row.get("Time") or "-")
            details = row.get("details") or []
            avatar = escape(title[:1].upper() if title else "?")
            detail_html = "".join(
                f"<div class='activity-detail'>{escape(str(detail))}</div>"
                for detail in details
                if str(detail).strip()
            )

            row_cols = st.columns([4.1, 1.5, 2.1, 1.0], gap="small")
            with row_cols[0]:
                avatar_col, text_col = st.columns([0.22, 3.78], gap="small")
                with avatar_col:
                    st.markdown(f"<div class='activity-avatar'>{avatar}</div>", unsafe_allow_html=True)
                with text_col:
                    st.markdown(f"<div class='activity-title'>{escape(title)}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='activity-subtitle'>{escape(subtitle)}</div>", unsafe_allow_html=True)
                    if detail_html:
                        st.markdown(detail_html, unsafe_allow_html=True)
            with row_cols[1]:
                st.markdown(status_badge(status), unsafe_allow_html=True)
            with row_cols[2]:
                st.markdown(f"<span class='branch-chip'>&#9679; {escape(branch)}</span>", unsafe_allow_html=True)
            with row_cols[3]:
                st.markdown(
                    f"<div class='time-cell' style='padding-top:0.2rem;'>{escape(time_label)}</div>",
                    unsafe_allow_html=True,
                )

            if index < len(records) - 1:
                st.divider()


def show_reference_data_table(
    records: list[dict[str, Any]],
    empty_message: str,
    *,
    headers: Sequence[str] | None = None,
    widths: Sequence[float] | None = None,
    right_align: Sequence[bool] | None = None,
) -> None:
    """Render a simple deployment-style data table without avatars or badges."""

    if not records:
        st.markdown(f"<div class='table-empty'>{escape(empty_message)}</div>", unsafe_allow_html=True)
        return

    frame = records_frame(records)
    column_names = list(frame.columns if headers is None else headers)
    if not column_names:
        st.markdown(f"<div class='table-empty'>{escape(empty_message)}</div>", unsafe_allow_html=True)
        return

    column_widths = list(widths or [1.0] * len(column_names))
    if len(column_widths) < len(column_names):
        column_widths.extend([1.0] * (len(column_names) - len(column_widths)))

    alignments = list(right_align or [False] * len(column_names))
    if len(alignments) < len(column_names):
        alignments.extend([False] * (len(column_names) - len(alignments)))

    with st.container(border=True):
        header_cols = st.columns(column_widths[: len(column_names)], gap="small")
        for column, label, align_right in zip(header_cols, column_names, alignments):
            with column:
                alignment = "right" if align_right else "left"
                st.markdown(
                    f"<div class='table-caption' style='margin-bottom:0; text-align:{alignment};'>{escape(str(label))}</div>",
                    unsafe_allow_html=True,
                )
        st.divider()

        for index, (_, row) in enumerate(frame.iterrows()):
            row_cols = st.columns(column_widths[: len(column_names)], gap="small")
            for col_idx, (column, align_right) in enumerate(zip(column_names, alignments)):
                with row_cols[col_idx]:
                    value = row[column]
                    if value is None or (isinstance(value, float) and pd.isna(value)):
                        text = "-"
                    else:
                        text = str(value)
                    alignment = "right" if align_right else "left"
                    st.markdown(
                        f"<div style='font-size:0.9rem; color:var(--text); text-align:{alignment}; padding-top:0.1rem;'>{escape(text)}</div>",
                        unsafe_allow_html=True,
                    )
            if index < len(frame) - 1:
                st.divider()


def metric_row(items: Sequence[tuple[str, Any]]) -> None:
    """Render one row of dashboard metrics using themed glass cards."""

    if not items:
        return
    columns = st.columns(len(items))
    for column, item in zip(columns, items):
        label, value = item
        with column:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{escape(str(label))}</div>
                    <div class="metric-value">{escape(str(value))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def resource_card(title: str, subtitle: str, meta: str, status: str, time_label: str) -> None:
    """Render one compact resource card similar to the reference dashboard."""

    st.markdown(
        f"""
        <div class="resource-card">
            <div class="resource-top">
                <div class="resource-icon">&#9634;</div>
                <div>
                    <div class="resource-title">{escape(title)}</div>
                    <div class="resource-subtitle">{escape(subtitle)}</div>
                </div>
            </div>
            <div class="resource-meta">{escape(meta)}</div>
            <div class="resource-footer">
                {status_badge(status)}
                <div class="resource-time">{escape(time_label)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def log_panel(title: str, lines: Sequence[str], *, eyebrow: str | None = None, badge: str | None = None) -> None:
    """Render a quiet activity log surface."""

    panel_header(title, "Recent activity from the current workspace.", eyebrow=eyebrow, badge=badge)
    if not lines:
        st.markdown("<div class='table-empty'>No recent activity is available.</div>", unsafe_allow_html=True)
        return

    body = "".join(f"<div class='log-line'>{escape(line)}</div>" for line in lines)
    st.markdown(f"<div class='log-panel'><div class='log-body'>{body}</div></div>", unsafe_allow_html=True)


def parse_optional_date(value: str | None) -> date | None:
    """Parse an ISO date string from backend output into a date object."""

    if not value:
        return None
    return date.fromisoformat(value)

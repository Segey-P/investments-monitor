# Integrated Investment & Asset Monitor: Master Specification

## 1\. Executive Summary

The Integrated Investment & Asset Monitor is a locally-hosted financial management system. It consolidates diverse asset classes—including registered and unregistered investment accounts, cryptocurrency, real estate, and liabilities—into a single analytics dashboard. The system prioritizes data privacy and security through local storage and password protection.

## 2\. Core Objectives

* **Centralization:** Aggregate holdings across RRSP, TFSA, Unregistered, and Crypto accounts.  
* **Leverage Oversight:** Specifically track HELOC utilization and its impact on portfolio risk.  
* **Net Worth Analysis:** Incorporate property values and mortgage balances for a holistic financial view.  
* **Privacy-First:** Ensure all sensitive financial data remains on the local machine.

## 3\. High-Level Architecture

| Component | Technology | Role |
| :---- | :---- | :---- |
| **Backend** | Python / SQLite | Manages local data storage and calculation of Adjusted Cost Base (ACB). |
| **Price Engine** | Yahoo Finance API (or similar) | Fetches real-time/delayed market prices for tickers. |
| **Web Interface** | Flask / FastAPI | Provides the interactive dashboard and portfolio views. |
| **Security Layer** | Basic Auth / Password | Restricts access to the local web interface. |

## 4\. Security & Data Integrity

* **Zero-Cloud Storage:** No financial data is to be synced to GitHub or cloud databases.  
* **Local Encryption:** (Optional/Future) Encrypt the SQLite database file.  
* **Manual Overrides:** Allow users to manually adjust prices or values for assets where API data is unavailable.


# Module 1: Investment & Leverage Engine Specification

## 1\. Objective

To manage the core investment data, calculate performance metrics, and track leveraged positions.

## 2\. Functional Requirements

### A. Account Management

* Support for multiple account types: RRSP, TFSA, Unregistered, and Crypto.  
* Ability to isolate portfolios (e.g., User Portfolio vs. future "Parents' Portfolio").

### B. Asset Tracking

* **Equity/ETF Tracking:** Input Ticker, Quantity, and Adjusted Cost Base (ACB).  
* **Crypto Tracking:** Manual or API-based tracking of coin holdings.  
* **Cash Management:** Tracking of uninvested cash balances per account.

### C. Leverage & HELOC Integration

* Dedicated ledger for HELOC drawdowns.  
* Calculation of "Leverage Ratio" (Total Debt vs. Total Invested Assets).  
* Interest expense tracking for tax-deductibility analysis (Unregistered accounts).

## 3\. Analytics & Breakdowns

The engine must calculate the following proportions:

* Cash vs. Individual Stocks vs. ETFs vs. Leveraged ETFs.  
* Sector concentration (if provided by API).  
* Total Unrealized Gain/Loss based on current market price vs. ACB.


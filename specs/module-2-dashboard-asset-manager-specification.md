# Module 2: Dashboard & Asset Manager Specification

## 1\. Objective

To provide a visual representation of financial health and manage non-market assets like property and mortgages.

## 2\. UI Components

### A. The "Cockpit" Dashboard

* **Total Net Worth:** Sum of all assets minus all liabilities.  
* **Allocation Pie Charts:** Visual breakdown of asset classes.  
* **Portfolio Selector:** Toggle between individual accounts or a consolidated "Family" view.

### B. Asset & Liability Ledger

* **Property Manager:** Manual entry for real estate value.  
* **Mortgage Tracker:** Manual entry for mortgage balance and interest rates.  
* **Risk Assessment:** Visualization of debt-to-equity across the entire household.

### C. Investment Watchlist

* A dedicated table for "Potential Buys."  
* Displays current price, 52-week high/low, and a user-defined "Target Buy Price."  
* Optional: Summary of recent price movement/volatility.

## 3\. Security Implementation

* **Login Screen:** A simple gateway requiring a password before the dashboard is rendered.  
* **Session Management:** Local session timeout to prevent unauthorized access if the browser is left open.


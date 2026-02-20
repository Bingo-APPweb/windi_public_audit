# WINDI Proof Shelf Definitions

Version: 1.0
Status: Normative

## Overview

Proof shelves are typed containers for canonicalized field values. Each shelf represents a specific semantic category of document data.

## Shelf Structure

```
TYPE|SUBTYPE|VALUE
```

- **TYPE**: Category identifier (uppercase)
- **SUBTYPE**: Format specifier (uppercase)
- **VALUE**: Canonicalized value

## Standard Shelf Types

### PAYTO — Payment Recipient

Identifies the payment destination account.

| Subtype | Description | Example Value |
|---------|-------------|---------------|
| `IBAN` | International Bank Account Number | `DE89370400440532013000` |
| `BIC` | Bank Identifier Code | `COBADEFFXXX` |
| `SWIFT` | SWIFT code (alias for BIC) | `COBADEFFXXX` |
| `ACCOUNT` | Generic account number | `1234567890` |

**Example:**
```
PAYTO|IBAN|DE89370400440532013000
```

### AMOUNT — Monetary Value

The transaction or invoice amount.

| Subtype | Description | Example Value |
|---------|-------------|---------------|
| `DEC` | Decimal (2 places) | `1234.50` |
| `INT` | Integer (cents) | `123450` |

**Example:**
```
AMOUNT|DEC|1234.50
```

### CURRENCY — Currency Code

ISO 4217 currency identifier.

| Subtype | Description | Example Value |
|---------|-------------|---------------|
| `ISO4217` | ISO 4217 alpha code | `EUR` |

**Example:**
```
CURRENCY|ISO4217|EUR
```

### DATE — Date/Time Values

Temporal identifiers.

| Subtype | Description | Example Value |
|---------|-------------|---------------|
| `ISO8601` | ISO 8601 date | `2026-02-07` |
| `ISO8601T` | ISO 8601 with time | `2026-02-07T14:30:00Z` |

**Example:**
```
DATE|ISO8601|2026-02-07
```

### REF — Reference Numbers

Document and transaction references.

| Subtype | Description | Example Value |
|---------|-------------|---------------|
| `INVOICE` | Invoice number | `INV-2026-001` |
| `ORDER` | Order number | `ORD-2026-001` |
| `CONTRACT` | Contract reference | `CTR-2026-001` |
| `CUSTOM` | Custom reference | `ABC123` |

**Example:**
```
REF|INVOICE|INV-2026-001
```

### PARTY — Involved Parties

Legal entities in the transaction.

| Subtype | Description | Example Value |
|---------|-------------|---------------|
| `NAME` | Legal name | `ACME GMBH` |
| `TAXID` | Tax identifier | `DE123456789` |
| `LEI` | Legal Entity Identifier | `5493001KJTIIGC8Y1R12` |

**Example:**
```
PARTY|NAME|ACME GMBH
```

### TEXT — Generic Text

Free-form text content.

| Subtype | Description | Example Value |
|---------|-------------|---------------|
| `UTF8` | UTF-8 normalized text | `Payment for services` |
| `UPPER` | Uppercase normalized | `PAYMENT FOR SERVICES` |

**Example:**
```
TEXT|UTF8|Payment for services
```

### STRUCT — Structural Metadata

Document structure information.

| Subtype | Description | Example Value |
|---------|-------------|---------------|
| `PAGECT` | Page count | `3` |
| `WORDCT` | Word count | `1250` |
| `CHECKSUM` | Content checksum | `abc123` |

**Example:**
```
STRUCT|PAGECT|3
```

## Custom Shelves

Organizations may define custom shelf types with the `X-` prefix:

```
X-MYORG|CUSTOM|value
```

Custom shelves MUST follow the same canonicalization rules.

## Shelf Ordering

When multiple shelves are combined (e.g., for structure hash):

1. Sort alphabetically by TYPE
2. Within same TYPE, sort by SUBTYPE
3. Join with newline (`\n`)

## Verification

During verification:

1. Extract field values from document
2. Apply canonicalization rules
3. Generate shelf string
4. Compute SHA-256 hash
5. Compare with ProofSet shelf hash

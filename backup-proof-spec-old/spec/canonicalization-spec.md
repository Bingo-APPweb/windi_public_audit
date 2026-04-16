# WINDI Canonicalization Specification

Version: 1.0
Status: Normative

## Purpose

Canonicalization ensures that identical semantic values always produce identical hashes, regardless of formatting variations in the source document.

## General Rules

1. **Encoding**: All text MUST be UTF-8 encoded
2. **Normalization**: Unicode NFC normalization MUST be applied
3. **Whitespace**: Leading/trailing whitespace MUST be trimmed
4. **Case**: Field-specific (see below)
5. **Separators**: Pipe character (`|`) separates shelf components

## Shelf Format

Each shelf follows the pattern:

```
TYPE|SUBTYPE|VALUE
```

Example:
```
PAYTO|IBAN|DE89370400440532013000
```

## Field-Specific Rules

### IBAN (Payment Account)

**Input variations:**
```
DE89 3704 0044 0532 0130 00
de89-3704-0044-0532-0130-00
DE89370400440532013000
```

**Canonicalization:**
1. Remove all whitespace and hyphens
2. Convert to uppercase
3. Validate check digits (optional)

**Canonical output:**
```
DE89370400440532013000
```

**Shelf format:**
```
PAYTO|IBAN|DE89370400440532013000
```

### Amount (Decimal)

**Input variations:**
```
1.234,50     (German format)
1,234.50     (US format)
1234.50      (No thousands separator)
€ 1.234,50   (With currency symbol)
```

**Canonicalization:**
1. Remove currency symbols and whitespace
2. Detect format by decimal separator position
3. Convert to period-decimal format
4. Round to 2 decimal places
5. Format with exactly 2 decimal digits

**Canonical output:**
```
1234.50
```

**Shelf format:**
```
AMOUNT|DEC|1234.50
```

### Currency

**Input variations:**
```
EUR
eur
Euro
€
```

**Canonicalization:**
1. Map symbols to ISO 4217 codes
2. Convert to uppercase
3. Validate against ISO 4217 list

**Canonical output:**
```
EUR
```

**Shelf format:**
```
CURRENCY|ISO4217|EUR
```

### Date

**Input variations:**
```
2026-02-07
07.02.2026
02/07/2026
7 Feb 2026
```

**Canonicalization:**
1. Parse to date object
2. Format as ISO 8601 (YYYY-MM-DD)

**Canonical output:**
```
2026-02-07
```

**Shelf format:**
```
DATE|ISO8601|2026-02-07
```

### Text (Generic)

**Canonicalization:**
1. Trim whitespace
2. Collapse multiple spaces to single space
3. Apply Unicode NFC normalization

**Shelf format:**
```
TEXT|UTF8|<normalized text>
```

## Hash Generation

After canonicalization:

1. Encode shelf string as UTF-8 bytes
2. Compute SHA-256 hash
3. Output as lowercase hexadecimal
4. Prefix with `sha256:`

```
sha256:<64 hex chars>
```

## Example: Complete Document

**Input document fields:**
```
IBAN:     DE89 3704 0044 0532 0130 00
Amount:   € 1.234,50
Currency: Euro
Date:     07.02.2026
```

**Canonicalized shelves:**
```
PAYTO|IBAN|DE89370400440532013000
AMOUNT|DEC|1234.50
CURRENCY|ISO4217|EUR
DATE|ISO8601|2026-02-07
```

**Shelf hashes:**
```
payto_hash:    sha256:8a7f... (hash of "PAYTO|IBAN|DE89370400440532013000")
amount_hash:   sha256:3b2e... (hash of "AMOUNT|DEC|1234.50")
currency_hash: sha256:9c4d... (hash of "CURRENCY|ISO4217|EUR")
date_hash:     sha256:1a5f... (hash of "DATE|ISO8601|2026-02-07")
```

## Reference Implementation

See `windi-reader-sdk/src/canonicalization.js` for the reference implementation.

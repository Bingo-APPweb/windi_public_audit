/**
 * WINDI Palette — Multi-Tenant Isolation E2E Tests
 * ==================================================
 * Verifies that tenant segregation is enforced in the UI and API layer.
 *
 * Test scenarios:
 * 1. Tenant selector changes active tenant context
 * 2. API requests include correct tenant_id
 * 3. Risk metrics are isolated per tenant
 * 4. Document exports carry tenant context
 *
 * Prerequisites:
 * - Palette UI running on localhost:8108
 * - Orchestrator running on localhost:8109
 * - Tenant selector implemented in UI with data-testid attributes
 *
 * 26 February 2026 — WINDI Governance Institute
 */

describe("WINDI Palette — Multi-Tenant Isolation", () => {
  const PALETTE_URL = "http://localhost:8108";
  const ORCHESTRATOR_URL = "http://localhost:8109";

  // Test tenants
  const TENANT_A = "siemens-pilot";
  const TENANT_B = "sparkasse-kempten";

  /**
   * Helper: Select a tenant in the UI
   */
  function selectTenant(tenantId) {
    cy.get('[data-testid="tenant-selector"]').click();
    cy.get(`[data-testid="tenant-option-${tenantId}"]`).click();
    cy.get('[data-testid="active-tenant"]').should("contain", tenantId);
  }

  /**
   * Helper: Send a chat message
   */
  function sendMessage(text) {
    cy.get('[data-testid="chat-input"]').clear().type(text);
    cy.get('[data-testid="send-btn"]').click();
  }

  /**
   * Helper: Extract tenant from request
   */
  function extractTenant(interception) {
    const header = interception.request.headers["x-windi-tenant"];
    const body = interception.request.body;
    return header || (body && body.tenant_id) || null;
  }

  beforeEach(() => {
    // Clear session storage to start fresh
    cy.clearLocalStorage();
    cy.clearCookies();
  });

  describe("Tenant Selector", () => {
    it("should display available tenants", () => {
      cy.visit(PALETTE_URL);
      cy.get('[data-testid="tenant-selector"]').should("exist");
      cy.get('[data-testid="tenant-selector"]').click();
      cy.get('[data-testid^="tenant-option-"]').should("have.length.at.least", 1);
    });

    it("should update active tenant when selected", () => {
      cy.visit(PALETTE_URL);
      selectTenant(TENANT_A);
      cy.get('[data-testid="active-tenant"]').should("contain", TENANT_A);
    });

    it("should persist tenant selection across page reload", () => {
      cy.visit(PALETTE_URL);
      selectTenant(TENANT_A);
      cy.reload();
      cy.get('[data-testid="active-tenant"]').should("contain", TENANT_A);
    });
  });

  describe("API Tenant Isolation", () => {
    it("should include tenant_id in chat requests", () => {
      cy.intercept("POST", "**/api/dragon/chat").as("chatRequest");

      cy.visit(PALETTE_URL);
      selectTenant(TENANT_A);
      sendMessage("Create a governance memo about risk assessment.");

      cy.wait("@chatRequest").then((interception) => {
        const tenant = extractTenant(interception);
        expect(tenant).to.equal(TENANT_A);
      });
    });

    it("should include tenant_id in orchestrate requests", () => {
      cy.intercept("POST", "**/orchestrate").as("orchestrateRequest");

      cy.visit(PALETTE_URL);
      selectTenant(TENANT_B);

      // Trigger document generation (adjust selector as needed)
      cy.get('[data-testid="generate-document-btn"]').click();
      cy.get('[data-testid="generate-submit"]').click();

      cy.wait("@orchestrateRequest").then((interception) => {
        const tenant = extractTenant(interception);
        expect(tenant).to.equal(TENANT_B);
      });
    });

    it("should switch tenant context between requests", () => {
      cy.intercept("POST", "**/api/dragon/chat").as("chatRequest");

      cy.visit(PALETTE_URL);

      // First tenant
      selectTenant(TENANT_A);
      sendMessage("Tenant A message");
      cy.wait("@chatRequest").then((interception) => {
        expect(extractTenant(interception)).to.equal(TENANT_A);
      });

      // Switch tenant
      selectTenant(TENANT_B);
      sendMessage("Tenant B message");
      cy.wait("@chatRequest").then((interception) => {
        expect(extractTenant(interception)).to.equal(TENANT_B);
      });
    });
  });

  describe("Risk Metrics Isolation", () => {
    it("should display risk metrics for active tenant only", () => {
      cy.intercept("POST", "**/api/dragon/chat").as("chatRequest");

      cy.visit(PALETTE_URL);
      selectTenant(TENANT_A);
      sendMessage("Analyze high-risk compliance scenario.");

      cy.wait("@chatRequest");

      // Risk summary should not show other tenant's data
      cy.get('[data-testid="risk-summary"]').should("not.contain", TENANT_B);

      // Risk timeline should be tenant-scoped
      cy.get('[data-testid="risk-timeline"]').within(() => {
        cy.get('[data-tenant]').each(($el) => {
          expect($el.attr("data-tenant")).to.equal(TENANT_A);
        });
      });
    });
  });

  describe("Document Export Isolation", () => {
    it("should include tenant context in exported documents", () => {
      cy.intercept("POST", "**/api/export/jmpg").as("exportRequest");

      cy.visit(PALETTE_URL);
      selectTenant(TENANT_A);

      // Trigger export
      cy.get('[data-testid="export-btn"]').click();
      cy.get('[data-testid="export-format-jmpg"]').click();
      cy.get('[data-testid="export-generate"]').click();

      cy.wait("@exportRequest").then((interception) => {
        const body = interception.request.body;
        expect(body.metadata).to.have.property("tenant_id", TENANT_A);
      });

      // Verify toast shows download
      cy.get('[data-testid="toast"]').should("contain", "downloaded");
    });
  });

  describe("Cross-Tenant Protection", () => {
    it("should not leak data between tenants", () => {
      cy.intercept("POST", "**/api/dragon/chat").as("chatRequest");

      cy.visit(PALETTE_URL);

      // Create data in Tenant A
      selectTenant(TENANT_A);
      const tenantAMessage = `Confidential Tenant A data ${Date.now()}`;
      sendMessage(tenantAMessage);
      cy.wait("@chatRequest");

      // Switch to Tenant B
      selectTenant(TENANT_B);

      // Verify Tenant A's message is not visible
      cy.get('[data-testid="chat-history"]').should("not.contain", tenantAMessage);

      // Decision journal should not show Tenant A decisions
      cy.get('[data-testid="decision-journal-btn"]').click();
      cy.get('[data-testid="decision-journal-list"]').should("not.contain", TENANT_A);
    });
  });

  describe("Orchestrator Integration", () => {
    it("should verify orchestrator health with multi-tenant config", () => {
      cy.request(`${ORCHESTRATOR_URL}/health`).then((response) => {
        expect(response.status).to.equal(200);
        expect(response.body.multi_tenant).to.exist;
        expect(response.body.multi_tenant.enabled).to.be.true;
        expect(response.body.multi_tenant.mode).to.equal("pipeline-isolated");
      });
    });

    it("should create tenant_context_receipt on orchestrate", () => {
      cy.request({
        method: "POST",
        url: `${ORCHESTRATOR_URL}/orchestrate`,
        body: {
          tenant_id: TENANT_A,
          prompt: "Generate test bulletin for Cypress",
          facts_verified: { test: "cypress" },
          auto_publish: true,
          human_ack: "I_APPROVE_PUBLISH"
        }
      }).then((response) => {
        expect(response.status).to.equal(200);
        expect(response.body.tenant_id).to.equal(TENANT_A);
        expect(response.body.steps.tenant_context_receipt).to.exist;
        expect(response.body.steps.tenant_context_receipt.status).to.equal("OK");
        expect(response.body.evidence.tenant_id).to.equal(TENANT_A);
      });
    });
  });
});

/**
 * WINDI Tenant Stamp E2E Tests
 * Validates tenant stamp presence in exports and tenant boundary alerts
 *
 * 26 February 2026 — WINDI Governance Institute
 */

describe('WINDI Tenant Stamp & Boundary', () => {

  beforeEach(() => {
    cy.visit('/palette/');
    // Wait for app to load
    cy.get('[data-testid="chat-input"], input[type="text"]', { timeout: 15000 }).should('be.visible');
  });

  describe('Tenant Stamp in Exports', () => {

    it('should include tenant stamp in JMPG manifest', () => {
      // Set tenant context
      cy.window().then(win => {
        if (win.WINDI_Tenant) {
          win.WINDI_Tenant.profile.tenant_id = 'test-tenant-stamp';
        }
      });

      // Generate a document
      cy.get('[data-testid="chat-input"], input[type="text"]')
        .type('Generate a brief governance note');
      cy.get('[data-testid="send-btn"], button').contains(/send|senden|enviar/i).click();

      // Wait for response
      cy.contains('🛡️', { timeout: 30000 }).should('be.visible');

      // Check that buildTenantStampManifest works
      cy.window().then(win => {
        const manifest = win.WINDI_TenantStamp?.buildManifest?.('test-tenant-stamp');
        expect(manifest).to.have.property('tenant');
        expect(manifest.tenant).to.have.property('id', 'test-tenant-stamp');
        expect(manifest.tenant).to.have.property('stamp', 'TENANT: TEST-TENANT-STAMP');
        expect(manifest.tenant).to.have.property('segregation_mode', 'forensic-metadata');
      });
    });

    it('should render tenant stamp element correctly', () => {
      cy.window().then(win => {
        // Create stamp element
        const stamp = win.WINDI_TenantStamp?.createElement?.({
          tenantId: 'barclays-pilot',
          mode: 'forensic-metadata',
          level: 'GOLD',
          isolationScore: 96
        }, 'klar');

        if (stamp) {
          // Verify stamp structure
          expect(stamp.querySelector('.windi-tenant-stamp__id').textContent).to.equal('BARCLAYS-PILOT');
          expect(stamp.querySelector('.windi-tenant-stamp__lvl').textContent).to.equal('GOLD');
          expect(stamp.querySelector('.windi-tenant-stamp__mode').textContent).to.equal('forensic-metadata');
          expect(stamp.querySelector('.windi-tenant-stamp__score').textContent).to.equal('96/100');
        }
      });
    });

    it('should apply KLAR theme styling', () => {
      cy.window().then(win => {
        win.WINDI_TenantStamp?.injectCSS?.();

        const stamp = win.WINDI_TenantStamp?.createElement?.({
          tenantId: 'test-klar',
          level: 'HIGH'
        }, 'klar');

        if (stamp) {
          document.body.appendChild(stamp);
          const styles = window.getComputedStyle(stamp);
          // KLAR theme should have light background
          expect(styles.background).to.include('linear-gradient');
          stamp.remove();
        }
      });
    });

    it('should apply NOIR theme styling', () => {
      cy.window().then(win => {
        win.WINDI_TenantStamp?.injectCSS?.();

        const stamp = win.WINDI_TenantStamp?.createElement?.({
          tenantId: 'test-noir',
          level: 'GOLD'
        }, 'noir');

        if (stamp) {
          document.body.appendChild(stamp);
          expect(stamp.classList.contains('windi-tenant-stamp--noir')).to.be.true;
          stamp.remove();
        }
      });
    });

  });

  describe('Tenant Boundary Alerts', () => {

    it('should track tenant and allow same-tenant messages', () => {
      cy.window().then(win => {
        // Reset audit state
        win.WINDI_TenantAudit?.reset?.();

        // Set initial tenant
        const result1 = win.WINDI_TenantAudit?.setActiveTenant?.('tenant-a');
        expect(result1).to.have.property('ok', true);
        expect(result1).to.have.property('firstSet', true);

        // Same tenant should be OK
        const result2 = win.WINDI_TenantAudit?.setActiveTenant?.('tenant-a');
        expect(result2).to.have.property('ok', true);
      });
    });

    it('should detect and alert on tenant boundary crossing', () => {
      cy.window().then(win => {
        // Reset audit state
        win.WINDI_TenantAudit?.reset?.();

        // Set initial tenant
        win.WINDI_TenantAudit?.setActiveTenant?.('tenant-a');

        // Try to switch tenant
        const result = win.WINDI_TenantAudit?.setActiveTenant?.('tenant-b');
        expect(result).to.have.property('ok', false);
        expect(result).to.have.property('boundaryAlert');
        expect(result.boundaryAlert).to.have.property('from', 'tenant-a');
        expect(result.boundaryAlert).to.have.property('to', 'tenant-b');
        expect(result.boundaryAlert).to.have.property('action', 'HUMAN_REVIEW_REQUIRED');
      });
    });

    it('should track boundary alerts in global summary', () => {
      cy.window().then(win => {
        win.WINDI_TenantAudit?.reset?.();

        // Create a boundary crossing
        win.WINDI_TenantAudit?.setActiveTenant?.('tenant-a');
        win.WINDI_TenantAudit?.setActiveTenant?.('tenant-b');

        const summary = win.WINDI_TenantAudit?.globalSummary?.();
        expect(summary).to.have.property('totalBoundaryAlerts', 1);
      });
    });

    it('should block send on tenant boundary in UI', () => {
      // Set initial tenant
      cy.window().then(win => {
        win.WINDI_TenantAudit?.reset?.();
        if (win.WINDI_Tenant) {
          win.WINDI_Tenant.profile.tenant_id = 'tenant-initial';
        }
      });

      // Send first message
      cy.get('[data-testid="chat-input"], input[type="text"]')
        .type('First message');
      cy.get('[data-testid="send-btn"], button').contains(/send|senden|enviar/i).click();

      // Wait for response
      cy.contains('🛡️', { timeout: 30000 }).should('be.visible');

      // Change tenant
      cy.window().then(win => {
        if (win.WINDI_Tenant) {
          win.WINDI_Tenant.profile.tenant_id = 'tenant-different';
        }
      });

      // Try to send another message
      cy.get('[data-testid="chat-input"], input[type="text"]')
        .type('Second message with different tenant');
      cy.get('[data-testid="send-btn"], button').contains(/send|senden|enviar/i).click();

      // Should see boundary alert
      cy.contains(/tenant boundary|mandantengrenze|limite de tenant/i, { timeout: 10000 })
        .should('be.visible');
    });

  });

  describe('Tenant Isolation Score', () => {

    it('should calculate isolation score correctly', () => {
      cy.window().then(win => {
        win.WINDI_TenantAudit?.reset?.();

        // Set up a tenant with good isolation
        win.WINDI_TenantAudit?.setActiveTenant?.('good-tenant');
        win.WINDI_TenantAudit?.trackReceipt?.({
          id: 'receipt-1',
          governance_level: 'HIGH',
          metadata: { tenant_id: 'good-tenant' }
        });

        const score = win.WINDI_TenantAudit?.isolationScore?.('good-tenant');
        expect(score).to.have.property('score');
        expect(score.score).to.be.at.least(90); // No conflicts, no alerts
        expect(score).to.have.property('status', 'excellent');
      });
    });

    it('should penalize conflicts in isolation score', () => {
      cy.window().then(win => {
        win.WINDI_TenantAudit?.reset?.();

        // Track same document in two tenants (conflict)
        win.WINDI_TenantAudit?.setActiveTenant?.('tenant-x');
        win.WINDI_TenantAudit?.trackReceipt?.({
          id: 'receipt-conflict',
          com_id: 'COM-CONFLICT',
          governance_level: 'HIGH',
          metadata: { tenant_id: 'tenant-x' }
        });

        win.WINDI_TenantAudit?.setActiveTenant?.('tenant-y', { reason: 'test' });
        win.WINDI_TenantAudit?.trackReceipt?.({
          id: 'receipt-conflict-2',
          com_id: 'COM-CONFLICT', // Same com_id!
          governance_level: 'HIGH',
          metadata: { tenant_id: 'tenant-y' }
        });

        // Check that conflict is detected
        const summary = win.WINDI_TenantAudit?.globalSummary?.();
        expect(summary.totalConflicts).to.be.at.least(1);

        // Score should be penalized
        const scoreX = win.WINDI_TenantAudit?.isolationScore?.('tenant-x');
        expect(scoreX.conflicts).to.be.at.least(1);
        expect(scoreX.score).to.be.lessThan(70); // -40 for conflict
      });
    });

  });

  describe('Tenant Badge Visibility', () => {

    it('should show tenant badge in message GovChips', () => {
      // Set tenant
      cy.window().then(win => {
        if (win.WINDI_Tenant) {
          win.WINDI_Tenant.profile.tenant_id = 'badge-test-tenant';
        }
      });

      // Generate a response
      cy.get('[data-testid="chat-input"], input[type="text"]')
        .type('Hello');
      cy.get('[data-testid="send-btn"], button').contains(/send|senden|enviar/i).click();

      // Wait for response with tenant badge
      cy.contains('🏢', { timeout: 30000 }).should('be.visible');
      cy.contains('badge-test-tenant').should('be.visible');
    });

  });

});

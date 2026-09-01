/**
 * Creator Discovery & AI Outreach Application Logic
 * Integrates FastAPI Intelligence, Gemini Outreach, and Official Meta Instagram Messaging
 * 
 * Strict Invariants:
 * 1. PUBLIC DISCOVERY != META MESSAGING IDENTITY != MESSAGE SENDABILITY
 * 2. Never infers or fabricates an IGSID from a username.
 * 3. Never claims success without official Meta 200/201 acknowledgment.
 * 4. Clear separation between Real Meta Mode and Local Simulation Mode.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Elements - Navigation & Health
  const statusYt = document.getElementById("status-yt");
  const statusGemini = document.getElementById("status-gemini");
  const statusMeta = document.getElementById("status-meta");
  const modeToggleBtn = document.getElementById("mode-toggle-btn");
  const consoleModeBadge = document.getElementById("console-mode-badge");
  const workspaceModeText = document.getElementById("workspace-mode-text");

  // Elements - Discovery Form
  const discoveryForm = document.getElementById("discovery-form");
  const creatorUrlInput = document.getElementById("creator-url-input");
  const clearInputBtn = document.getElementById("clear-input-btn");
  const findCreatorBtn = document.getElementById("find-creator-btn");
  const sampleChips = document.querySelectorAll(".sample-chip");

  // Elements - Progress & Error Banner
  const pipelineProgress = document.getElementById("pipeline-progress");
  const pipelineStatusText = document.getElementById("pipeline-status-text");
  const progressBarFill = document.getElementById("progress-bar-fill");
  const errorBanner = document.getElementById("error-banner");
  const errorTitle = document.getElementById("error-title");
  const errorMessage = document.getElementById("error-message");
  const dismissErrorBtn = document.getElementById("dismiss-error-btn");

  // Elements - Workspace Container
  const creatorWorkspace = document.getElementById("creator-workspace");
  const viewHistoryBtn = document.getElementById("view-history-btn");
  const viewEvidenceTrailBtn = document.getElementById("view-evidence-trail-btn");

  // Elements - Creator Profile Card
  const creatorAvatarImg = document.getElementById("creator-avatar-img");
  const creatorAvatarFallback = document.getElementById("creator-avatar-fallback");
  const creatorName = document.getElementById("creator-name");
  const creatorHandle = document.getElementById("creator-handle");
  const creatorProfileLink = document.getElementById("creator-profile-link");
  const creatorSubscribersVal = document.getElementById("creator-subscribers-val");
  const creatorViewsVal = document.getElementById("creator-views-val");
  const metricRecentContent = document.getElementById("metric-recent-content");
  const creatorRecentTitle = document.getElementById("creator-recent-title");
  const creatorBioText = document.getElementById("creator-bio-text");

  // Elements - Contact Information
  const emailStatusPill = document.getElementById("email-status-pill");
  const emailFoundView = document.getElementById("email-found-view");
  const emailNotFoundView = document.getElementById("email-not-found-view");
  const discoveredEmailAddress = document.getElementById("discovered-email-address");
  const copyEmailBtn = document.getElementById("copy-email-btn");
  const emailEvidenceText = document.getElementById("email-evidence-text");

  const igDiscoveryPill = document.getElementById("ig-discovery-pill");
  const igFoundView = document.getElementById("ig-found-view");
  const igNotFoundView = document.getElementById("ig-not-found-view");
  const discoveredIgUsername = document.getElementById("discovered-ig-username");
  const openIgLink = document.getElementById("open-ig-link");
  const igEvidenceText = document.getElementById("ig-evidence-text");
  const quickSendIgBtn = document.getElementById("quick-send-ig-btn");
  const quickSendBtnLabel = document.getElementById("quick-send-btn-label");
  const igCardCapabilityBadge = document.getElementById("ig-card-capability-badge");
  const igCardCapabilityHint = document.getElementById("ig-card-capability-hint");
  const openMetaRulesBtn = document.getElementById("open-meta-rules-btn");

  const otherSocialsCard = document.getElementById("other-socials-card");
  const otherSocialsCount = document.getElementById("other-socials-count");
  const toggleOtherSocials = document.getElementById("toggle-other-socials");
  const otherSocialsContent = document.getElementById("other-socials-content");
  const otherSocialsGrid = document.getElementById("other-socials-grid");

  // Elements - AI Outreach
  const sendAiOutreachBtn = document.getElementById("send-ai-outreach-btn");
  const sendAiBtnText = document.getElementById("send-ai-btn-text");
  const regenerateOutreachBtn = document.getElementById("regenerate-outreach-btn");
  const editOutreachBtn = document.getElementById("edit-outreach-btn");
  const editBtnText = document.getElementById("edit-btn-text");
  const copyOutreachBtn = document.getElementById("copy-outreach-btn");
  const outreachTextarea = document.getElementById("outreach-textarea");
  const charCountVal = document.getElementById("char-count-val");
  const groundingEvidenceList = document.getElementById("grounding-evidence-list");
  const directDraftSendBar = document.getElementById("direct-draft-send-bar");
  const draftTargetHandle = document.getElementById("draft-target-handle");
  const directSendDraftBtn = document.getElementById("direct-send-draft-btn");

  // Elements - Instagram Messaging Console
  const messagingEligibilityPill = document.getElementById("messaging-eligibility-pill");
  const eligibilityBanner = document.getElementById("eligibility-banner");
  const eligibilityBannerTitle = document.getElementById("eligibility-banner-title");
  const eligibilityBannerDesc = document.getElementById("eligibility-banner-desc");
  const eligibilityBannerIcon = document.getElementById("eligibility-banner-icon");
  const altOutreachBanner = document.getElementById("alt-outreach-banner");
  const useEmailOutreachBtn = document.getElementById("use-email-outreach-btn");

  const consoleDiscoveryVal = document.getElementById("console-discovery-val");
  const consoleRecipientVal = document.getElementById("console-recipient-val");
  const consoleCapabilityVal = document.getElementById("console-capability-val");

  const tabTestMsg = document.getElementById("tab-test-msg");
  const tabAiMsg = document.getElementById("tab-ai-msg");
  const activeDispatchTextarea = document.getElementById("active-dispatch-textarea");
  const activeMsgTypeLabel = document.getElementById("active-msg-type-label");

  const toggleRecipientIdBtn = document.getElementById("toggle-recipient-id-btn");
  const recipientIdDrawer = document.getElementById("recipient-id-drawer");
  const customIgsidInput = document.getElementById("custom-igsid-input");
  const applyIgsidBtn = document.getElementById("apply-igsid-btn");

  const sendStatusDisplay = document.getElementById("send-status-display");
  const sendInstagramBtn = document.getElementById("send-instagram-btn");
  const sendBtnMainLabel = document.getElementById("send-btn-main-label");
  const sendResultCard = document.getElementById("send-result-card");
  const resultIcon = document.getElementById("result-icon");
  const resultTitle = document.getElementById("result-title");
  const resultMessage = document.getElementById("result-message");
  const resultMetaInfo = document.getElementById("result-meta-info");
  const resultMsgId = document.getElementById("result-msg-id");
  const resultModeLbl = document.getElementById("result-mode-lbl");
  const resultTimestamp = document.getElementById("result-timestamp");
  const resultProviderLbl = document.getElementById("result-provider-lbl");
  const retrySendBtn = document.getElementById("retry-send-btn");
  const openIgContinueBtn = document.getElementById("open-ig-continue-btn");

  // Elements - Quick Instagram Send Modal & Card Button
  const quickSendModal = document.getElementById("quick-send-modal");
  const quickSendModalSubtitle = document.getElementById("quick-send-modal-subtitle");
  const closeQuickSendModalBtn = document.getElementById("close-quick-send-modal-btn");
  const quickModalRecipientUsername = document.getElementById("quick-modal-recipient-username");
  const quickModalSenderAccount = document.getElementById("quick-modal-sender-account");
  const quickModalEligibilityBox = document.getElementById("quick-modal-eligibility-box");
  const quickModalStatusBadge = document.getElementById("quick-modal-status-badge");
  const quickModalStatusExplanation = document.getElementById("quick-modal-status-explanation");
  const quickModalTextarea = document.getElementById("quick-modal-textarea");
  const quickModalResultCard = document.getElementById("quick-modal-result-card");
  const quickResultIcon = document.getElementById("quick-result-icon");
  const quickResultTitle = document.getElementById("quick-result-title");
  const quickResultMessage = document.getElementById("quick-result-message");
  const quickResultMetaInfo = document.getElementById("quick-result-meta-info");
  const quickResultMsgId = document.getElementById("quick-result-msg-id");
  const quickResultMode = document.getElementById("quick-result-mode");
  const quickResultTimestamp = document.getElementById("quick-result-timestamp");
  const cardCopyMsgBtn = document.getElementById("card-copy-msg-btn");
  const consoleCopyMsgBtn = document.getElementById("console-copy-msg-btn");
  const quickModalCancelBtn = document.getElementById("quick-modal-cancel-btn");
  const quickModalOpenIgBtn = document.getElementById("quick-modal-open-ig-btn");
  const quickModalCopyMsgBtn = document.getElementById("quick-modal-copy-msg-btn");
  const quickModalSendBtn = document.getElementById("quick-modal-send-btn");
  const quickSendModalBtnText = document.getElementById("quick-send-modal-btn-text");

  // Elements - Educational Meta Rules Modal
  const metaRulesModal = document.getElementById("meta-rules-modal");
  const closeMetaRulesBtn = document.getElementById("close-meta-rules-btn");
  const dismissMetaRulesBtn = document.getElementById("dismiss-meta-rules-btn");

  // Elements - Evidence Trail & Modals
  const evidenceTrailSection = document.getElementById("evidence-trail-section");
  const closeEvidenceBtn = document.getElementById("close-evidence-btn");
  const evidenceTableTbody = document.getElementById("evidence-table-tbody");
  const historyModal = document.getElementById("history-modal");
  const closeHistoryModalBtn = document.getElementById("close-history-modal-btn");
  const historyList = document.getElementById("history-list");

  // State
  let activeGlobalMode = "real"; // "real" or "simulation"
  let currentExtraction = null;
  let currentDiscoveredUsername = null;
  let activeRecipientIgsid = null;
  let currentEligibility = null;
  let connectedAccountId = null;
  let isEditingOutreach = false;
  let activeMessageType = "outreach"; // "test" or "outreach"
  let isSendingActive = false;

  const DEFAULT_TEST_MESSAGE = "Hi! This is a test message from my AI creator outreach application.";

  // Platform Icons Map
  const PLATFORM_ICONS = {
    instagram: "fa-brands fa-instagram",
    twitter: "fa-brands fa-x-twitter",
    tiktok: "fa-brands fa-tiktok",
    facebook: "fa-brands fa-facebook",
    linkedin: "fa-brands fa-linkedin",
    threads: "fa-brands fa-threads",
    discord: "fa-brands fa-discord",
    telegram: "fa-brands fa-telegram",
    twitch: "fa-brands fa-twitch",
    reddit: "fa-brands fa-reddit",
    snapchat: "fa-brands fa-snapchat",
    pinterest: "fa-brands fa-pinterest",
    patreon: "fa-brands fa-patreon",
    github: "fa-brands fa-github",
    spotify: "fa-brands fa-spotify",
    linktree: "fa-solid fa-tree",
    generic: "fa-solid fa-globe"
  };

  // ==========================================
  // 1. Initial Health Check & Diagnostics
  // ==========================================
  async function checkSystemHealth() {
    try {
      const res = await fetch("/api/health");
      if (res.ok) {
        const data = await res.json();
        updateStatusPill(statusYt, data.youtube_api_configured, "YouTube API");
        updateStatusPill(statusGemini, data.gemini_api_configured, "Gemini AI");
        updateStatusPill(statusMeta, data.meta_api_configured, "Meta API");
      }
    } catch (e) {
      console.warn("Health check error:", e);
    }

    try {
      const igStatusRes = await fetch("/api/social/instagram/status");
      if (igStatusRes.ok) {
        const igData = await igStatusRes.json();
        connectedAccountId = igData.account_id || null;
      }
    } catch (e) {
      console.warn("Instagram status error:", e);
    }
  }

  function updateStatusPill(el, isConfigured, label) {
    if (!el) return;
    el.classList.remove("checking");
    if (isConfigured) {
      el.className = "status-pill online";
      el.innerHTML = `<span class="status-dot"></span> ${label}: Active`;
    } else {
      el.className = "status-pill offline";
      el.innerHTML = `<span class="status-dot"></span> ${label}: Fallback`;
    }
  }

  checkSystemHealth();

  // Mode Switcher Handler
  if (modeToggleBtn) {
    modeToggleBtn.addEventListener("click", () => {
      activeGlobalMode = activeGlobalMode === "real" ? "simulation" : "real";
      applyModeUI();
      if (currentDiscoveredUsername) {
        checkInstagramEligibility(currentDiscoveredUsername, activeRecipientIgsid);
      }
    });
  }

  function applyModeUI() {
    if (activeGlobalMode === "real") {
      modeToggleBtn.className = "mode-toggle-btn real-active";
      consoleModeBadge.className = "mode-badge real";
      consoleModeBadge.textContent = "REAL META API";
      workspaceModeText.textContent = "Mode: Official Meta Graph API";
      if (quickSendBtnLabel) quickSendBtnLabel.textContent = "Send Test Message";
    } else {
      modeToggleBtn.className = "mode-toggle-btn sim-active";
      consoleModeBadge.className = "mode-badge sim";
      consoleModeBadge.textContent = "LOCAL SIMULATION";
      workspaceModeText.textContent = "Mode: Local Simulation (No Meta Calls)";
      if (quickSendBtnLabel) quickSendBtnLabel.textContent = "Simulate Message";
    }
  }

  // ==========================================
  // 2. Input Form & Quick Samples
  // ==========================================
  if (creatorUrlInput && clearInputBtn) {
    creatorUrlInput.addEventListener("input", () => {
      clearInputBtn.style.display = creatorUrlInput.value.trim() ? "block" : "none";
    });

    clearInputBtn.addEventListener("click", () => {
      creatorUrlInput.value = "";
      clearInputBtn.style.display = "none";
      creatorUrlInput.focus();
    });
  }

  if (sampleChips) {
    sampleChips.forEach(chip => {
      chip.addEventListener("click", () => {
        const url = chip.getAttribute("data-url");
        if (url && creatorUrlInput) {
          creatorUrlInput.value = url;
          if (clearInputBtn) clearInputBtn.style.display = "block";
          if (discoveryForm) discoveryForm.dispatchEvent(new Event("submit"));
        }
      });
    });
  }

  // ==========================================
  // 3. Extraction Pipeline Trigger
  // ==========================================
  if (discoveryForm) {
    discoveryForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const inputUrl = creatorUrlInput ? creatorUrlInput.value.trim() : "";
      if (!inputUrl) return;

      hideError();
      startProgressAnimation();
      setSearchingState(true);
      if (creatorWorkspace) creatorWorkspace.style.display = "none";
      if (evidenceTrailSection) evidenceTrailSection.style.display = "none";
      if (sendResultCard) sendResultCard.style.display = "none";
      activeRecipientIgsid = null;
      if (customIgsidInput) customIgsidInput.value = "";

      try {
        const response = await fetch("/api/extract", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: inputUrl })
        });

        const result = await response.json();
        finishProgressAnimation();
        setSearchingState(false);

        if (result.success && result.data) {
          currentExtraction = result.data;
          renderCreatorWorkspace(result.data);
        } else {
          showError("Extraction Failed", result.error || "Could not retrieve creator metadata from the provided link.");
        }
      } catch (err) {
        finishProgressAnimation();
        setSearchingState(false);
        showError("Connection Error", `Failed to contact intelligence server: ${err.message}`);
      }
    });
  }

  function setSearchingState(isSearching) {
    if (!findCreatorBtn) return;
    findCreatorBtn.disabled = isSearching;
    const label = findCreatorBtn.querySelector(".btn-label");
    const loading = findCreatorBtn.querySelector(".btn-loading");
    if (label) label.style.display = isSearching ? "none" : "inline-flex";
    if (loading) loading.style.display = isSearching ? "inline-flex" : "none";
  }

  // Animated Progress Pipeline
  let progressInterval = null;
  function startProgressAnimation() {
    if (pipelineProgress) pipelineProgress.style.display = "block";
    if (progressBarFill) progressBarFill.style.width = "5%";
    
    const stages = [
      { text: "Resolving YouTube URL & channel handle...", pct: 20 },
      { text: "Fetching official YouTube metadata & descriptions...", pct: 45 },
      { text: "Extracting RFC verified business emails & social links...", pct: 70 },
      { text: "Enriching creator context with Google Gemini AI...", pct: 90 },
      { text: "Assembling verified contact intelligence...", pct: 98 }
    ];

    let stageIdx = 0;
    if (pipelineStatusText) pipelineStatusText.textContent = stages[0].text;
    if (progressBarFill) progressBarFill.style.width = stages[0].pct + "%";

    progressInterval = setInterval(() => {
      stageIdx++;
      if (stageIdx < stages.length) {
        if (pipelineStatusText) pipelineStatusText.textContent = stages[stageIdx].text;
        if (progressBarFill) progressBarFill.style.width = stages[stageIdx].pct + "%";
      }
    }, 1200);
  }

  function finishProgressAnimation() {
    if (progressInterval) clearInterval(progressInterval);
    if (progressBarFill) progressBarFill.style.width = "100%";
    if (pipelineStatusText) pipelineStatusText.textContent = "Extraction complete!";
    setTimeout(() => {
      if (pipelineProgress) pipelineProgress.style.display = "none";
      if (progressBarFill) progressBarFill.style.width = "0%";
    }, 500);
  }

  function showError(title, msg) {
    if (errorTitle) errorTitle.textContent = title;
    if (errorMessage) errorMessage.textContent = msg;
    if (errorBanner) {
      errorBanner.style.display = "flex";
      errorBanner.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }

  function hideError() {
    if (errorBanner) errorBanner.style.display = "none";
  }

  if (dismissErrorBtn) {
    dismissErrorBtn.addEventListener("click", hideError);
  }

  // ==========================================
  // 4. Render Creator Workspace
  // ==========================================
  function renderCreatorWorkspace(data) {
    const yt = data.youtube || {};
    const emails = data.emails || [];
    const socials = data.social_links || data.social_media || {};
    const evidence = data.evidence || [];

    // 1. Profile Card
    if (creatorName) creatorName.textContent = yt.channel_title || yt.title || "Creator Discovered";
    if (creatorHandle) creatorHandle.textContent = yt.custom_url ? `@${yt.custom_url.replace(/^@/, '')}` : (yt.channel_id || "");
    
    if (creatorProfileLink) {
      if (yt.url) {
        creatorProfileLink.href = yt.url;
        creatorProfileLink.style.display = "inline-flex";
      } else {
        creatorProfileLink.style.display = "none";
      }
    }

    if (creatorSubscribersVal) creatorSubscribersVal.textContent = yt.subscriber_count ? formatNumber(yt.subscriber_count) : "Hidden";
    if (creatorViewsVal) creatorViewsVal.textContent = yt.view_count ? formatNumber(yt.view_count) : "--";

    if (creatorRecentTitle && metricRecentContent) {
      if (yt.video_title) {
        creatorRecentTitle.textContent = yt.video_title;
        metricRecentContent.style.display = "flex";
      } else {
        metricRecentContent.style.display = "none";
      }
    }

    if (creatorBioText) {
      creatorBioText.textContent = yt.description ? yt.description.slice(0, 240) + (yt.description.length > 240 ? "..." : "") : "No public bio or description available for this account.";
    }

    if (yt.thumbnail_url && creatorAvatarImg && creatorAvatarFallback) {
      creatorAvatarImg.src = yt.thumbnail_url;
      creatorAvatarImg.style.display = "block";
      creatorAvatarFallback.style.display = "none";
    } else if (creatorAvatarImg && creatorAvatarFallback) {
      creatorAvatarImg.style.display = "none";
      creatorAvatarFallback.style.display = "flex";
    }

    // 2. Email Section
    renderEmailSection(emails);

    // 3. Instagram Section
    renderInstagramSection(socials.instagram);

    // 4. Other Socials Accordion
    renderOtherSocials(socials);

    // 5. Evidence Trail
    renderEvidenceTrail(evidence);

    // 6. Generate AI Outreach
    generateAiOutreach(data);

    // 7. Check Instagram Messaging Eligibility
    const igAcc = socials.instagram;
    let igHandle = null;
    if (igAcc) {
      if (igAcc.username) {
        igHandle = igAcc.username.replace(/^@/, "").trim();
      } else if (igAcc.url) {
        const match = igAcc.url.match(/instagram\.com\/([a-zA-Z0-9_.-]+)/i);
        if (match && !["p", "reel", "stories", "explore", "direct"].includes(match[1].toLowerCase())) {
          igHandle = match[1];
        }
      }
    }

    if (igHandle) {
      checkInstagramEligibility(igHandle, null);
    } else {
      renderEligibilityUI({
        discovery: { status: "not_discovered" },
        recipient: { status: "unresolved" },
        capability: {
          status: "not_messageable",
          reason: "No Instagram account was discovered for this creator.",
          can_attempt_send: false
        },
        can_send: false
      });
    }

    if (creatorWorkspace) {
      creatorWorkspace.style.display = "flex";
      creatorWorkspace.scrollIntoView({ behavior: "smooth" });
    }
  }

  function formatNumber(num) {
    const n = Number(num);
    if (isNaN(n)) return String(num);
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
    if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
    return n.toLocaleString();
  }

  // ==========================================
  // 5. Email Section Rendering
  // ==========================================
  function renderEmailSection(emails) {
    if (emails && emails.length > 0) {
      const primaryEmail = emails[0];
      if (discoveredEmailAddress) discoveredEmailAddress.textContent = primaryEmail.email;
      if (emailEvidenceText) {
        emailEvidenceText.textContent = primaryEmail.evidence
          ? `Source: ${primaryEmail.source} ("${primaryEmail.evidence.slice(0, 50)}...")`
          : `Source: ${primaryEmail.source}`;
      }

      if (emailStatusPill) {
        emailStatusPill.className = "pill-badge pill-success";
        emailStatusPill.innerHTML = `<i class="fa-solid fa-circle-check"></i> Discovered (${emails.length})`;
      }

      if (emailFoundView) emailFoundView.style.display = "block";
      if (emailNotFoundView) emailNotFoundView.style.display = "none";
    } else {
      if (emailStatusPill) {
        emailStatusPill.className = "pill-badge pill-neutral";
        emailStatusPill.textContent = "Not Found";
      }

      if (emailFoundView) emailFoundView.style.display = "none";
      if (emailNotFoundView) emailNotFoundView.style.display = "block";
    }
  }

  if (copyEmailBtn) {
    copyEmailBtn.addEventListener("click", () => {
      const text = discoveredEmailAddress ? discoveredEmailAddress.textContent : "";
      if (text) {
        navigator.clipboard.writeText(text);
        copyEmailBtn.innerHTML = `<i class="fa-solid fa-check"></i> Copied`;
        setTimeout(() => {
          copyEmailBtn.innerHTML = `<i class="fa-regular fa-copy"></i> Copy`;
        }, 2000);
      }
    });
  }

  // ==========================================
  // 6. Instagram Section Rendering (Separation of Discovery vs Capability)
  // ==========================================
  function renderInstagramSection(igAccount) {
    let handle = null;
    if (igAccount) {
      if (igAccount.username) {
        handle = igAccount.username.replace(/^@/, "").trim();
      } else if (igAccount.url) {
        const match = igAccount.url.match(/instagram\.com\/([a-zA-Z0-9_.-]+)/i);
        if (match && !["p", "reel", "stories", "explore", "direct"].includes(match[1].toLowerCase())) {
          handle = match[1];
        }
      }
    }

    if (handle) {
      currentDiscoveredUsername = handle;
      if (discoveredIgUsername) discoveredIgUsername.textContent = handle;
      if (openIgLink) openIgLink.href = igAccount.url || `https://instagram.com/${handle}`;
      if (igEvidenceText) {
        igEvidenceText.textContent = `Discovered via ${igAccount.source || 'YouTube metadata'} (${igAccount.confidence || 'High'} Confidence)`;
      }

      if (igDiscoveryPill) {
        igDiscoveryPill.className = "pill-badge pill-success";
        igDiscoveryPill.innerHTML = `<i class="fa-solid fa-circle-check"></i> Discovered`;
      }

      if (igFoundView) igFoundView.style.display = "block";
      if (igNotFoundView) igNotFoundView.style.display = "none";

      if (consoleDiscoveryVal) {
        consoleDiscoveryVal.textContent = `@${handle}`;
        consoleDiscoveryVal.className = "console-meta-value highlight-ig";
      }

      if (draftTargetHandle) draftTargetHandle.textContent = `@${handle}`;
      if (directDraftSendBar) directDraftSendBar.style.display = "flex";
    } else {
      currentDiscoveredUsername = null;
      if (igDiscoveryPill) {
        igDiscoveryPill.className = "pill-badge pill-neutral";
        igDiscoveryPill.textContent = "Not Found";
      }

      if (igFoundView) igFoundView.style.display = "none";
      if (igNotFoundView) igNotFoundView.style.display = "block";

      if (consoleDiscoveryVal) {
        consoleDiscoveryVal.textContent = "Not Discovered";
        consoleDiscoveryVal.className = "console-meta-value text-muted";
      }

      if (draftTargetHandle) draftTargetHandle.textContent = "Not Discovered";
      if (directDraftSendBar) directDraftSendBar.style.display = "none";
    }
  }

  // ==========================================
  // 7. Other Social Media Accordion
  // ==========================================
  function renderOtherSocials(socials) {
    const otherKeys = Object.keys(socials).filter(k => k !== "instagram");
    if (otherKeys.length > 0) {
      if (otherSocialsCount) otherSocialsCount.textContent = otherKeys.length;
      if (otherSocialsGrid) {
        otherSocialsGrid.innerHTML = "";

        otherKeys.forEach(platform => {
          const item = socials[platform];
          const iconClass = PLATFORM_ICONS[platform] || PLATFORM_ICONS.generic;
          const displayName = platform.charAt(0).toUpperCase() + platform.slice(1);
          const handleText = item.username ? `@${item.username}` : displayName;

          const badge = document.createElement("a");
          badge.className = "social-badge-link";
          badge.href = item.url;
          badge.target = "_blank";
          badge.rel = "noopener noreferrer";
          badge.innerHTML = `<i class="${iconClass}"></i> <span>${handleText}</span> <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 10px; opacity: 0.7;"></i>`;
          otherSocialsGrid.appendChild(badge);
        });
      }

      if (otherSocialsCard) otherSocialsCard.style.display = "block";
    } else {
      if (otherSocialsCard) otherSocialsCard.style.display = "none";
    }
  }

  if (toggleOtherSocials && otherSocialsContent) {
    toggleOtherSocials.addEventListener("click", () => {
      const isOpen = otherSocialsContent.style.display === "block";
      otherSocialsContent.style.display = isOpen ? "none" : "block";
      toggleOtherSocials.classList.toggle("open", !isOpen);
    });
  }

  // ==========================================
  // 8. AI Outreach Generator
  // ==========================================
  async function generateAiOutreach(data) {
    const yt = data.youtube || {};
    if (regenerateOutreachBtn) {
      regenerateOutreachBtn.disabled = true;
      const rotateIcon = regenerateOutreachBtn.querySelector("i");
      if (rotateIcon) rotateIcon.classList.add("fa-spin");
    }

    try {
      const payload = {
        creator_name: yt.channel_title || yt.title || "Creator",
        channel_name: yt.channel_title || yt.title || "YouTube Channel",
        platform: "YouTube",
        category: "Creator",
        recent_video_title: yt.video_title || null,
        description_snippet: yt.description ? yt.description.slice(0, 300) : null,
        sender_name: "Partnerships Team"
      };

      const res = await fetch("/api/outreach/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const outreach = await res.json();
        if (outreachTextarea) outreachTextarea.value = outreach.message || "";
        updateCharCount();

        if (groundingEvidenceList) {
          groundingEvidenceList.innerHTML = "";
          (outreach.grounded_evidence || []).forEach(item => {
            const pill = document.createElement("span");
            pill.className = "grounding-pill";
            pill.innerHTML = `<i class="fa-solid fa-check"></i> ${escapeHtml(item)}`;
            groundingEvidenceList.appendChild(pill);
          });
        }

        if (activeMessageType === "outreach" && activeDispatchTextarea && outreachTextarea) {
          activeDispatchTextarea.value = outreachTextarea.value;
        }
      }
    } catch (e) {
      console.warn("Outreach generation failed:", e);
    } finally {
      if (regenerateOutreachBtn) {
        regenerateOutreachBtn.disabled = false;
        const rotateIcon = regenerateOutreachBtn.querySelector("i");
        if (rotateIcon) rotateIcon.classList.remove("fa-spin");
      }
    }
  }

  if (regenerateOutreachBtn) {
    regenerateOutreachBtn.addEventListener("click", () => {
      if (currentExtraction) generateAiOutreach(currentExtraction);
    });
  }

  if (editOutreachBtn) {
    editOutreachBtn.addEventListener("click", () => {
      isEditingOutreach = !isEditingOutreach;
      if (isEditingOutreach) {
        if (outreachTextarea) outreachTextarea.focus();
        if (editBtnText) editBtnText.textContent = "Done";
        editOutreachBtn.classList.add("active-edit");
      } else {
        if (editBtnText) editBtnText.textContent = "Edit";
        editOutreachBtn.classList.remove("active-edit");
      }
    });
  }

  if (outreachTextarea) {
    outreachTextarea.addEventListener("input", () => {
      updateCharCount();
      if (activeDispatchTextarea && activeMessageType === "outreach") {
        activeDispatchTextarea.value = outreachTextarea.value;
      }
      if (quickModalTextarea) {
        quickModalTextarea.value = outreachTextarea.value;
      }
    });
  }

  if (activeDispatchTextarea) {
    activeDispatchTextarea.addEventListener("input", () => {
      if (activeMessageType === "outreach" && outreachTextarea) {
        outreachTextarea.value = activeDispatchTextarea.value;
        updateCharCount();
      }
    });
  }

  if (sendAiOutreachBtn) {
    sendAiOutreachBtn.addEventListener("click", () => {
      const msg = (outreachTextarea && outreachTextarea.value.trim()) || (activeDispatchTextarea && activeDispatchTextarea.value.trim()) || "";
      if (!msg) {
        alert("Please generate or enter an outreach message before sending.");
        return;
      }
      executeInstagramSend(msg, "draft_header");
    });
  }

  if (directSendDraftBtn) {
    directSendDraftBtn.addEventListener("click", () => {
      const msg = (outreachTextarea && outreachTextarea.value.trim()) || (activeDispatchTextarea && activeDispatchTextarea.value.trim()) || "";
      if (!msg) {
        alert("Please generate or enter an outreach message before sending.");
        return;
      }
      executeInstagramSend(msg, "draft_footer");
    });
  }

  if (copyOutreachBtn) {
    copyOutreachBtn.addEventListener("click", () => {
      const text = outreachTextarea ? outreachTextarea.value : "";
      if (text) {
        navigator.clipboard.writeText(text);
        const span = copyOutreachBtn.querySelector("span");
        if (span) span.textContent = "Copied ✓";
        setTimeout(() => { if (span) span.textContent = "Copy"; }, 2000);
      }
    });
  }

  if (useEmailOutreachBtn) {
    useEmailOutreachBtn.addEventListener("click", () => {
      const text = outreachTextarea ? outreachTextarea.value : "";
      if (text) {
        navigator.clipboard.writeText(text);
        useEmailOutreachBtn.innerHTML = `<i class="fa-solid fa-check"></i> Outreach Copied to Clipboard!`;
        setTimeout(() => {
          useEmailOutreachBtn.innerHTML = `<i class="fa-solid fa-copy"></i> Copy Outreach for Email`;
        }, 2500);
      }
    });
  }

  if (outreachTextarea) {
    outreachTextarea.addEventListener("input", updateCharCount);
  }

  function updateCharCount() {
    if (charCountVal && outreachTextarea) {
      charCountVal.textContent = outreachTextarea.value.length;
    }
    if (activeMessageType === "outreach" && activeDispatchTextarea && outreachTextarea) {
      activeDispatchTextarea.value = outreachTextarea.value;
    }
  }

  // ==========================================
  // 9. Instagram Messaging Capability & Eligibility
  // ==========================================
  async function checkInstagramEligibility(username, user_id) {
    if (messagingEligibilityPill) {
      messagingEligibilityPill.className = "eligibility-status-pill pill-neutral";
      messagingEligibilityPill.innerHTML = `<span class="pill-dot"></span> Checking Meta Eligibility...`;
    }

    if (igCardCapabilityBadge) {
      igCardCapabilityBadge.className = "pill-badge pill-neutral";
      igCardCapabilityBadge.textContent = "Checking Meta Eligibility";
    }

    if (quickModalStatusBadge) {
      quickModalStatusBadge.className = "pill-badge pill-neutral";
      quickModalStatusBadge.textContent = "Checking Meta Eligibility";
      if (quickModalStatusExplanation) {
        quickModalStatusExplanation.textContent = "Validating recipient eligibility with Meta Instagram Graph API...";
      }
    }

    try {
      const creatorId = currentExtraction?.youtube?.channel_id || currentExtraction?.channel_id || currentExtraction?.creator_id || "";
      const queryParams = new URLSearchParams({
        instagram_username: username || "",
        creator_id: creatorId,
        mode: activeGlobalMode
      });

      const res = await fetch(`/api/instagram/outreach/status?${queryParams.toString()}`);
      if (res.ok) {
        const data = await res.json();
        currentEligibility = data;
        renderEligibilityUI(data);
        renderQuickModalEligibilityUI(data);
      } else {
        const fallback = {
          mode: activeGlobalMode,
          discovery: { status: "discovered", username: username },
          delivery: {
            method: "manual_instagram",
            messageable: false,
            status: "manual_instagram_required",
            label: "Instagram — manual send",
            details: "Instagram profile discovered. Official Meta API validation performed on send."
          },
          messaging: { eligible: false, status: "manual_send_required", reason: "Instagram Found" }
        };
        currentEligibility = fallback;
        renderEligibilityUI(fallback);
        renderQuickModalEligibilityUI(fallback);
      }
    } catch (e) {
      const fallback = {
        mode: activeGlobalMode,
        discovery: { status: "discovered", username: username },
        delivery: {
          method: "manual_instagram",
          messageable: false,
          status: "manual_instagram_required",
          label: "Instagram — manual send",
          details: "Instagram profile discovered. Official Meta API validation performed on send."
        },
        messaging: { eligible: false, status: "manual_send_required", reason: "Instagram Found" }
      };
      currentEligibility = fallback;
      renderEligibilityUI(fallback);
      renderQuickModalEligibilityUI(fallback);
    }
  }

  function renderEligibilityUI(data) {
    const discovery = data.discovery || { username: data.instagram_username ? data.instagram_username.replace(/^@/, '') : currentDiscoveredUsername };
    const delivery = data.delivery || {
      method: (data.messaging && data.messaging.eligible) ? "meta_api" : "manual_instagram",
      messageable: Boolean(data.messaging && data.messaging.eligible),
      label: (data.messaging && data.messaging.eligible) ? "Instagram — Meta API" : "Instagram — manual send",
      details: (data.messaging && data.messaging.reason) || "Instagram Found."
    };

    const isSim = activeGlobalMode === "simulation";
    const isMeta = !isSim && (delivery.method === "meta_api" || (data.messaging && data.messaging.eligible));
    const hasHandle = Boolean(discovery.username || currentDiscoveredUsername);

    // 1. Console Meta Fields
    if (consoleDiscoveryVal) {
      consoleDiscoveryVal.textContent = hasHandle ? `@${(discovery.username || currentDiscoveredUsername).replace(/^@/, '')}` : "Not Discovered";
      consoleDiscoveryVal.className = hasHandle ? "console-meta-value highlight-ig" : "console-meta-value text-muted";
    }

    // 2. Messaging & Delivery Mode Handling
    if (isSim) {
      if (messagingEligibilityPill) {
        messagingEligibilityPill.className = "eligibility-status-pill eligible";
        messagingEligibilityPill.innerHTML = `<span class="pill-dot"></span> Eligible (Simulation)`;
      }
      if (eligibilityBanner) {
        eligibilityBanner.className = "eligibility-banner eligible-mode";
        if (eligibilityBannerIcon) eligibilityBannerIcon.className = "fa-solid fa-flask banner-status-icon";
        if (eligibilityBannerTitle) eligibilityBannerTitle.textContent = "⚡ Simulation Mode Active";
        if (eligibilityBannerDesc) eligibilityBannerDesc.textContent = "Test outreach pipeline locally without making external Meta API calls.";
      }
      if (consoleRecipientVal) {
        consoleRecipientVal.textContent = "Eligible (Simulation)";
        consoleRecipientVal.className = "console-meta-value highlight-ig";
      }
      if (consoleCapabilityVal) {
        consoleCapabilityVal.textContent = "Local Simulation";
        consoleCapabilityVal.className = "console-meta-value highlight-ig";
      }

      if (sendInstagramBtn) {
        sendInstagramBtn.style.display = "inline-flex";
        sendInstagramBtn.disabled = false;
      }
      if (sendBtnMainLabel) sendBtnMainLabel.innerHTML = `<i class="fa-solid fa-flask"></i> Simulate Send`;
      if (openIgContinueBtn) openIgContinueBtn.style.display = "none";
      if (consoleCopyMsgBtn) consoleCopyMsgBtn.style.display = "inline-flex";

      if (sendStatusDisplay) {
        sendStatusDisplay.innerHTML = `<span style="color: #c084fc;"><i class="fa-solid fa-flask"></i> Simulation ready</span>`;
      }
      if (altOutreachBanner) altOutreachBanner.style.display = "none";
      if (igCardCapabilityBadge) {
        igCardCapabilityBadge.className = "pill-badge pill-neutral";
        igCardCapabilityBadge.textContent = "Eligible (Sim)";
      }
      if (igCardCapabilityHint) igCardCapabilityHint.textContent = "Simulate message pipeline without external Meta API calls.";
      if (quickSendBtnLabel) quickSendBtnLabel.textContent = "Send Message";

    } else if (isMeta) {
      if (messagingEligibilityPill) {
        messagingEligibilityPill.className = "eligibility-status-pill eligible";
        messagingEligibilityPill.innerHTML = `<span class="pill-dot"></span> Eligible (Meta API)`;
      }

      if (eligibilityBanner) {
        eligibilityBanner.className = "eligibility-banner eligible-mode";
        if (eligibilityBannerIcon) eligibilityBannerIcon.className = "fa-solid fa-circle-check banner-status-icon";
        if (eligibilityBannerTitle) eligibilityBannerTitle.textContent = "✓ Recipient Eligible (Connected Meta Conversation Active)";
        if (eligibilityBannerDesc) eligibilityBannerDesc.textContent = delivery.details || "Official Meta Graph API messaging is ready for automated direct dispatch.";
      }

      if (consoleRecipientVal) {
        consoleRecipientVal.textContent = "Eligible";
        consoleRecipientVal.className = "console-meta-value highlight-ig";
      }
      if (consoleCapabilityVal) {
        consoleCapabilityVal.textContent = "Instagram — Meta API";
        consoleCapabilityVal.className = "console-meta-value highlight-ig";
      }

      if (sendInstagramBtn) {
        sendInstagramBtn.style.display = "inline-flex";
        sendInstagramBtn.disabled = false;
      }
      if (sendBtnMainLabel) sendBtnMainLabel.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Send Message`;
      if (openIgContinueBtn) openIgContinueBtn.style.display = "none";
      if (consoleCopyMsgBtn) consoleCopyMsgBtn.style.display = "inline-flex";

      if (sendStatusDisplay) {
        sendStatusDisplay.innerHTML = `<span style="color: #34d399;"><i class="fa-solid fa-check"></i> Eligible for official Meta API send</span>`;
      }
      if (altOutreachBanner) altOutreachBanner.style.display = "none";

      if (igCardCapabilityBadge) {
        igCardCapabilityBadge.className = "pill-badge pill-success";
        igCardCapabilityBadge.textContent = "Eligible";
      }
      if (igCardCapabilityHint) igCardCapabilityHint.textContent = "Connected Meta messaging session active and ready for delivery.";
      if (quickSendBtnLabel) quickSendBtnLabel.textContent = "Send Message";

    } else if (hasHandle) {
      const igHandle = (discovery.username || currentDiscoveredUsername).replace(/^@/, '');
      if (messagingEligibilityPill) {
        messagingEligibilityPill.className = "eligibility-status-pill pill-neutral";
        messagingEligibilityPill.innerHTML = `<span class="pill-dot"></span> Instagram Found`;
      }

      if (eligibilityBanner) {
        eligibilityBanner.className = "eligibility-banner info-mode";
        if (eligibilityBannerIcon) eligibilityBannerIcon.className = "fa-brands fa-instagram banner-status-icon";
        if (eligibilityBannerTitle) eligibilityBannerTitle.textContent = `Instagram Found (@${igHandle})`;
        if (eligibilityBannerDesc) eligibilityBannerDesc.textContent = `Discovered Instagram profile for this creator. Click "Send Message" to attempt delivery through Meta's official Instagram Graph API.`;
      }

      if (consoleRecipientVal) {
        consoleRecipientVal.textContent = "Instagram Found";
        consoleRecipientVal.className = "console-meta-value highlight-ig";
      }
      if (consoleCapabilityVal) {
        consoleCapabilityVal.textContent = "Official Meta API";
        consoleCapabilityVal.className = "console-meta-value highlight-ig";
      }

      // Keep Send button enabled so backend evaluates official Meta eligibility on send
      if (sendInstagramBtn) {
        sendInstagramBtn.style.display = "inline-flex";
        sendInstagramBtn.disabled = false;
      }
      if (sendBtnMainLabel) sendBtnMainLabel.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Send Message`;
      if (openIgContinueBtn) openIgContinueBtn.style.display = "none";
      if (consoleCopyMsgBtn) consoleCopyMsgBtn.style.display = "inline-flex";

      if (sendStatusDisplay) {
        sendStatusDisplay.innerHTML = `<span style="color: #38bdf8;"><i class="fa-solid fa-circle-info"></i> Instagram account found. Click Send Message to dispatch via Meta API.</span>`;
      }
      if (altOutreachBanner) altOutreachBanner.style.display = "none";

      if (igCardCapabilityBadge) {
        igCardCapabilityBadge.className = "pill-badge pill-neutral";
        igCardCapabilityBadge.textContent = "Instagram Found";
      }
      if (igCardCapabilityHint) igCardCapabilityHint.textContent = "Discovered from public profile links. Official Meta API validation evaluated on send.";
      if (quickSendBtnLabel) quickSendBtnLabel.textContent = "Send Message";

    } else {
      if (messagingEligibilityPill) {
        messagingEligibilityPill.className = "eligibility-status-pill pill-neutral";
        messagingEligibilityPill.innerHTML = `<span class="pill-dot"></span> Not Discovered`;
      }

      if (eligibilityBanner) {
        eligibilityBanner.className = "eligibility-banner info-mode";
        if (eligibilityBannerIcon) eligibilityBannerIcon.className = "fa-solid fa-circle-info banner-status-icon";
        if (eligibilityBannerTitle) eligibilityBannerTitle.textContent = "No Instagram Profile Discovered";
        if (eligibilityBannerDesc) eligibilityBannerDesc.textContent = "An Instagram handle must be identified before outreach can be sent.";
      }

      if (consoleRecipientVal) {
        consoleRecipientVal.textContent = "Not Discovered";
        consoleRecipientVal.className = "console-meta-value text-muted";
      }
      if (consoleCapabilityVal) {
        consoleCapabilityVal.textContent = "None";
        consoleCapabilityVal.className = "console-meta-value text-muted";
      }

      if (sendInstagramBtn) sendInstagramBtn.style.display = "none";
      if (openIgContinueBtn) openIgContinueBtn.style.display = "none";
      if (consoleCopyMsgBtn) consoleCopyMsgBtn.style.display = "none";

      if (sendStatusDisplay) sendStatusDisplay.textContent = "No Instagram recipient found";
      if (altOutreachBanner) altOutreachBanner.style.display = "none";

      if (igCardCapabilityBadge) {
        igCardCapabilityBadge.className = "pill-badge pill-neutral";
        igCardCapabilityBadge.textContent = "Not Discovered";
      }
      if (igCardCapabilityHint) igCardCapabilityHint.textContent = "No Instagram profile discovered.";
      if (quickSendBtnLabel) quickSendBtnLabel.textContent = "Send Message";
    }
  }

  function renderQuickModalEligibilityUI(data) {
    if (!quickSendModal) return;

    const username = data.instagram_username ? data.instagram_username.replace(/^@/, '') : currentDiscoveredUsername;
    const delivery = data.delivery || {
      method: (data.messaging && data.messaging.eligible) ? "meta_api" : "manual_instagram",
      messageable: Boolean(data.messaging && data.messaging.eligible),
      label: (data.messaging && data.messaging.eligible) ? "Instagram — Meta API" : "Instagram — manual send",
      details: (data.messaging && data.messaging.reason) || "Outreach ready."
    };

    const isSim = activeGlobalMode === "simulation";
    const isMeta = !isSim && (delivery.method === "meta_api" || (data.messaging && data.messaging.eligible));

    if (quickModalRecipientUsername) {
      quickModalRecipientUsername.textContent = username ? `@${username}` : "None";
    }

    if (isSim) {
      if (quickModalEligibilityBox) quickModalEligibilityBox.className = "quick-eligibility-box eligible";
      if (quickModalStatusBadge) {
        quickModalStatusBadge.className = "pill-badge pill-neutral";
        quickModalStatusBadge.innerHTML = `<i class="fa-solid fa-flask"></i> Local Simulation`;
      }
      if (quickModalStatusExplanation) {
        quickModalStatusExplanation.textContent = "Simulation mode active. Test pipeline dispatch locally without external Meta API calls.";
      }
      if (quickModalSendBtn) {
        quickModalSendBtn.style.display = "inline-flex";
        quickModalSendBtn.disabled = false;
      }
      if (quickSendModalBtnText) quickSendModalBtnText.innerHTML = `<i class="fa-solid fa-flask"></i> Simulate Send`;
      if (quickModalOpenIgBtn) quickModalOpenIgBtn.style.display = "none";
      if (quickModalCopyMsgBtn) quickModalCopyMsgBtn.style.display = "inline-flex";

    } else if (isMeta) {
      if (quickModalEligibilityBox) quickModalEligibilityBox.className = "quick-eligibility-box eligible";
      if (quickModalStatusBadge) {
        quickModalStatusBadge.className = "pill-badge pill-success";
        quickModalStatusBadge.innerHTML = `<i class="fa-solid fa-circle-check"></i> Eligible (Meta API)`;
      }
      if (quickModalStatusExplanation) {
        quickModalStatusExplanation.textContent = delivery.details || "Connected Meta messaging identity is active and ready for automated direct dispatch.";
      }
      if (quickModalSendBtn) {
        quickModalSendBtn.style.display = "inline-flex";
        quickModalSendBtn.disabled = false;
      }
      if (quickSendModalBtnText) quickSendModalBtnText.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Send Message`;
      if (quickModalOpenIgBtn) quickModalOpenIgBtn.style.display = "none";
      if (quickModalCopyMsgBtn) quickModalCopyMsgBtn.style.display = "inline-flex";

    } else {
      if (quickModalEligibilityBox) quickModalEligibilityBox.className = "quick-eligibility-box neutral";
      if (quickModalStatusBadge) {
        quickModalStatusBadge.className = "pill-badge pill-neutral";
        quickModalStatusBadge.innerHTML = `<i class="fa-brands fa-instagram"></i> Instagram Found`;
      }
      if (quickModalStatusExplanation) {
        quickModalStatusExplanation.innerHTML = `Discovered Instagram profile for @${username || 'creator'}. Click <strong>"Send Message"</strong> to attempt delivery through Meta's official Graph API.`;
      }
      if (quickModalSendBtn) {
        quickModalSendBtn.style.display = "inline-flex";
        quickModalSendBtn.disabled = false;
      }
      if (quickSendModalBtnText) quickSendModalBtnText.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Send Message`;
      if (quickModalOpenIgBtn) quickModalOpenIgBtn.style.display = "none";
      if (quickModalCopyMsgBtn) quickModalCopyMsgBtn.style.display = "inline-flex";
    }
  }

  // ==========================================
  // Quick Send Dialog Management
  // ==========================================
  function openInstagramTestMessageDialog() {
    if (!currentDiscoveredUsername) {
      alert("No Instagram account has been discovered yet.");
      return;
    }

    if (quickModalRecipientUsername) {
      quickModalRecipientUsername.textContent = `@${currentDiscoveredUsername.replace(/^@/, '')}`;
    }
    
    // Pre-populate with generated AI outreach if available, else default test message
    if (outreachTextarea && outreachTextarea.value.trim()) {
      quickModalTextarea.value = outreachTextarea.value.trim();
    } else {
      quickModalTextarea.value = DEFAULT_TEST_MESSAGE;
    }

    if (quickModalResultCard) quickModalResultCard.style.display = "none";
    if (quickResultMetaInfo) quickResultMetaInfo.style.display = "none";

    checkInstagramEligibility(currentDiscoveredUsername, activeRecipientIgsid);

    if (quickSendModal) {
      quickSendModal.style.display = "flex";
      setTimeout(() => {
        if (quickModalTextarea) quickModalTextarea.focus();
      }, 100);
    }
  }

  function closeInstagramTestMessageDialog() {
    if (quickSendModal) quickSendModal.style.display = "none";
  }

  if (quickSendIgBtn) {
    quickSendIgBtn.addEventListener("click", openInstagramTestMessageDialog);
  }

  if (closeQuickSendModalBtn) {
    closeQuickSendModalBtn.addEventListener("click", closeInstagramTestMessageDialog);
  }

  if (quickModalCancelBtn) {
    quickModalCancelBtn.addEventListener("click", closeInstagramTestMessageDialog);
  }

  if (quickModalCopyMsgBtn) {
    quickModalCopyMsgBtn.addEventListener("click", () => {
      const text = (quickModalTextarea && quickModalTextarea.value) || "";
      if (text) {
        navigator.clipboard.writeText(text);
        quickModalCopyMsgBtn.innerHTML = `<i class="fa-solid fa-check"></i> Copied ✓`;
        setTimeout(() => {
          quickModalCopyMsgBtn.innerHTML = `<i class="fa-regular fa-copy"></i> Copy Message`;
        }, 2000);
      }
    });
  }

  if (quickSendModal) {
    quickSendModal.addEventListener("click", (e) => {
      if (e.target === quickSendModal) {
        closeInstagramTestMessageDialog();
      }
    });
  }

  // Educational Meta Rules Modal Handlers
  if (openMetaRulesBtn) {
    openMetaRulesBtn.addEventListener("click", () => {
      if (metaRulesModal) metaRulesModal.style.display = "flex";
    });
  }

  if (closeMetaRulesBtn) {
    closeMetaRulesBtn.addEventListener("click", () => {
      if (metaRulesModal) metaRulesModal.style.display = "none";
    });
  }

  if (dismissMetaRulesBtn) {
    dismissMetaRulesBtn.addEventListener("click", () => {
      if (metaRulesModal) metaRulesModal.style.display = "none";
    });
  }

  if (metaRulesModal) {
    metaRulesModal.addEventListener("click", (e) => {
      if (e.target === metaRulesModal) {
        metaRulesModal.style.display = "none";
      }
    });
  }

  // Keyboard shortcut: Escape to close all modals
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (quickSendModal && quickSendModal.style.display === "flex") {
        closeInstagramTestMessageDialog();
      }
      if (historyModal && historyModal.style.display === "flex") {
        historyModal.style.display = "none";
      }
      if (metaRulesModal && metaRulesModal.style.display === "flex") {
        metaRulesModal.style.display = "none";
      }
    }
  });

  // Tabs: Test Message vs AI Outreach Message
  if (tabTestMsg) {
    tabTestMsg.addEventListener("click", () => {
      activeMessageType = "test";
      tabTestMsg.classList.add("active");
      if (tabAiMsg) tabAiMsg.classList.remove("active");
      if (activeMsgTypeLabel) activeMsgTypeLabel.textContent = "Fixed Test DM";
      if (activeDispatchTextarea) activeDispatchTextarea.value = DEFAULT_TEST_MESSAGE;
    });
  }

  if (tabAiMsg) {
    tabAiMsg.addEventListener("click", () => {
      activeMessageType = "outreach";
      tabAiMsg.classList.add("active");
      if (tabTestMsg) tabTestMsg.classList.remove("active");
      if (activeMsgTypeLabel) activeMsgTypeLabel.textContent = "Customized AI Outreach";
      if (activeDispatchTextarea) activeDispatchTextarea.value = (outreachTextarea ? outreachTextarea.value : "");
    });
  }

  // ==========================================
  // 10. Outreach Actions: Official Meta API Send & Fallback Flow
  // ==========================================

  // A) Manual Instagram Handoff Workflow
  async function handleManualInstagramHandoff(msgText, triggerSource = "console") {
    const cleanMsg = (msgText || "").trim();
    if (!cleanMsg) {
      alert("Please enter a message before continuing.");
      return;
    }

    if (!currentDiscoveredUsername) {
      alert("No Instagram username is available for this creator.");
      return;
    }

    const cleanUser = currentDiscoveredUsername.replace(/^@/, "").trim();
    const profileUrl = `https://www.instagram.com/${cleanUser}/`;

    // 1. Copy message to clipboard
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(cleanMsg);
      }
    } catch (clipErr) {
      console.warn("Clipboard write failed:", clipErr);
    }

    // 2. Open Instagram Profile in new tab
    window.open(profileUrl, "_blank", "noopener,noreferrer");

    // 3. Record auditable entry via backend without claiming sent
    try {
      await fetch("/api/instagram/outreach/prepare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          creator_id: currentExtraction?.youtube?.channel_id || currentExtraction?.channel_id || currentExtraction?.creator_id || null,
          creator_username: cleanUser,
          creator_url: profileUrl,
          message: cleanMsg,
          action: "profile_opened_copied"
        })
      });
    } catch (apiErr) {
      console.warn("Could not log outreach prepare audit:", apiErr);
    }

    // 4. Update UI to show ready / opened state
    if (sendStatusDisplay) {
      sendStatusDisplay.innerHTML = `<span style="color: #38bdf8; font-weight: 600;"><i class="fa-solid fa-arrow-up-right-from-square"></i> Instagram profile opened. Your personalized message is ready to paste.</span>`;
    }

    const manualResult = {
      success: true,
      status: "prepared",
      delivery_method: "manual_instagram",
      provider: "instagram_direct",
      message: `Instagram opened for @${cleanUser}. Your personalized message is copied to clipboard and ready to paste.`,
      details: "Profile opened in a new tab. Paste your prepared message to complete outreach."
    };

    renderSendResult(manualResult);
    if (quickModalResultCard) {
      renderQuickModalSendResult(manualResult);
    }
  }

  // B) Automated Official Meta API Dispatch
  async function executeInstagramSend(msgToSend, triggerSource = "console") {
    if (isSendingActive) return; // Prevent double-clicks
    const cleanMsg = (msgToSend || "").trim();
    if (!cleanMsg) {
      alert("Please provide a message text before sending.");
      return;
    }

    await executeOfficialMetaSend(cleanMsg, triggerSource);
  }

  async function executeOfficialMetaSend(cleanMsg, triggerSource = "modal") {
    isSendingActive = true;
    setSendingState(true, "Sending...");
    setQuickModalSendingState(true);

    if (sendResultCard) sendResultCard.style.display = "none";
    if (resultMetaInfo) resultMetaInfo.style.display = "none";
    if (quickModalResultCard) quickModalResultCard.style.display = "none";

    const cleanUser = currentDiscoveredUsername ? currentDiscoveredUsername.replace(/^@/, "").trim() : null;
    const creatorNameVal = currentExtraction?.youtube?.channel_title || currentExtraction?.youtube?.title || currentExtraction?.creator_name || null;
    const creatorIdVal = currentExtraction?.youtube?.channel_id || currentExtraction?.channel_id || currentExtraction?.creator_id || null;
    const igUrlVal = currentExtraction?.social_links?.instagram?.url || (cleanUser ? `https://www.instagram.com/${cleanUser}/` : null);

    const payload = {
      creator_name: creatorNameVal,
      creator_id: creatorIdVal,
      instagram_username: cleanUser,
      instagram_url: igUrlVal,
      instagram_user_id: activeRecipientIgsid || null,
      message: cleanMsg,
      message_type: activeMessageType || "outreach",
      mode: activeGlobalMode || "real",
      idempotency_key: `send_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    let responseData = null;
    let fetchError = null;

    try {
      // Call dedicated endpoint POST /api/outreach/instagram/send
      const response = await fetch("/api/outreach/instagram/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      responseData = await response.json();
    } catch (err) {
      clearTimeout(timeoutId);
      fetchError = err;
    } finally {
      isSendingActive = false;
      setSendingState(false);
      setQuickModalSendingState(false);
    }

    if (fetchError) {
      const isTimeout = fetchError.name === "AbortError";
      const errResult = {
        success: false,
        status: "failed",
        error_code: isTimeout ? "TIMEOUT" : "CONNECTION_ERROR",
        provider: "meta",
        error: isTimeout
          ? "Request timed out contacting the messaging backend. Please try again."
          : "Unable to contact the messaging backend. Please check your connection and try again."
      };
      try {
        renderSendResult(errResult);
        renderQuickModalSendResult(errResult);
      } catch (uiErr) {
        console.error("UI rendering error:", uiErr);
      }
    } else if (responseData) {
      try {
        renderSendResult(responseData);
        renderQuickModalSendResult(responseData);
      } catch (uiErr) {
        console.error("UI rendering error:", uiErr);
      }
    }
  }

  // Hook up Action Buttons
  if (openIgContinueBtn) {
    openIgContinueBtn.addEventListener("click", () => {
      const msg = (activeDispatchTextarea && activeDispatchTextarea.value) || (outreachTextarea ? outreachTextarea.value : "");
      handleManualInstagramHandoff(msg, "console");
    });
  }

  if (quickModalOpenIgBtn) {
    quickModalOpenIgBtn.addEventListener("click", () => {
      const msg = (quickModalTextarea && quickModalTextarea.value) || "";
      handleManualInstagramHandoff(msg, "modal");
    });
  }

  if (sendInstagramBtn) {
    sendInstagramBtn.addEventListener("click", () => {
      executeInstagramSend(activeDispatchTextarea ? activeDispatchTextarea.value : "", "console");
    });
  }

  if (quickModalSendBtn) {
    quickModalSendBtn.addEventListener("click", () => {
      executeInstagramSend(quickModalTextarea ? quickModalTextarea.value : "", "modal");
    });
  }

  if (consoleCopyMsgBtn) {
    consoleCopyMsgBtn.addEventListener("click", () => {
      const text = (activeDispatchTextarea && activeDispatchTextarea.value.trim()) || DEFAULT_TEST_MESSAGE;
      navigator.clipboard.writeText(text).then(() => {
        consoleCopyMsgBtn.innerHTML = `<i class="fa-solid fa-check"></i> Copied ✓`;
        setTimeout(() => {
          consoleCopyMsgBtn.innerHTML = `<i class="fa-regular fa-copy"></i> Copy Message`;
        }, 2000);
      });
    });
  }

  function setSendingState(isSending, statusMsg = "") {
    if (sendInstagramBtn) {
      sendInstagramBtn.disabled = isSending;
      const btnText = sendInstagramBtn.querySelector(".btn-text");
      const btnSpinner = sendInstagramBtn.querySelector(".btn-spinner");
      if (btnText) btnText.style.display = isSending ? "none" : "inline-flex";
      if (btnSpinner) btnSpinner.style.display = isSending ? "inline-flex" : "none";
    }
    if (sendAiOutreachBtn) {
      sendAiOutreachBtn.disabled = isSending;
      if (sendAiBtnText) sendAiBtnText.textContent = isSending ? "Sending..." : "Send Message";
    }
    if (directSendDraftBtn) {
      directSendDraftBtn.disabled = isSending;
      const btnText = directSendDraftBtn.querySelector(".btn-text");
      const btnSpinner = directSendDraftBtn.querySelector(".btn-spinner");
      if (btnText) btnText.style.display = isSending ? "none" : "inline-flex";
      if (btnSpinner) btnSpinner.style.display = isSending ? "inline-flex" : "none";
    }
    if (sendStatusDisplay) {
      if (isSending) {
        sendStatusDisplay.innerHTML = `<span style="color: #818cf8;"><i class="fa-solid fa-circle-notch fa-spin"></i> ${statusMsg || "Sending..."}</span>`;
      }
    }
  }

  function setQuickModalSendingState(isSending) {
    if (!quickModalSendBtn) return;
    quickModalSendBtn.disabled = isSending;
    const btnText = quickModalSendBtn.querySelector(".btn-text");
    const btnSpinner = quickModalSendBtn.querySelector(".btn-spinner");
    if (btnText) btnText.style.display = isSending ? "none" : "inline-flex";
    if (btnSpinner) btnSpinner.style.display = isSending ? "inline-flex" : "none";
  }

  function renderSendResult(res) {
    if (!sendResultCard) return;
    sendResultCard.style.display = "block";

    if (res.status === "prepared" || res.delivery_method === "manual_instagram") {
      sendResultCard.className = "send-result-card success-card";
      if (resultIcon) resultIcon.className = "fa-solid fa-arrow-up-right-from-square result-card-icon";
      if (resultTitle) resultTitle.textContent = "Instagram Profile Opened";
      if (resultMessage) resultMessage.textContent = res.message || "Instagram profile opened in a new tab. Your personalized message is copied to clipboard.";
      if (resultMetaInfo) resultMetaInfo.style.display = "none";
      if (retrySendBtn) retrySendBtn.style.display = "none";
      return;
    }

    if (res.success && res.status === "sent") {
      sendResultCard.className = "send-result-card success-card";
      if (resultIcon) resultIcon.className = "fa-solid fa-circle-check result-card-icon";
      if (resultTitle) resultTitle.textContent = "✓ Message sent";
      if (resultMessage) resultMessage.textContent = "Official Meta Graph API confirmed message delivery to the recipient.";
      
      if (resultMsgId) resultMsgId.textContent = res.message_id || "N/A";
      if (resultModeLbl) resultModeLbl.textContent = "REAL META API";
      if (resultTimestamp) resultTimestamp.textContent = res.sent_at ? new Date(res.sent_at).toLocaleTimeString() : new Date().toLocaleTimeString();
      if (resultProviderLbl) resultProviderLbl.textContent = "Meta Graph API";
      if (resultMetaInfo) resultMetaInfo.style.display = "flex";
      if (retrySendBtn) retrySendBtn.style.display = "none";

      if (sendStatusDisplay) {
        sendStatusDisplay.innerHTML = `<span style="color: #34d399; font-weight: 700;"><i class="fa-solid fa-check"></i> Message sent</span>`;
      }

    } else if (res.success && res.status === "simulated") {
      sendResultCard.className = "send-result-card success-card";
      if (resultIcon) resultIcon.className = "fa-solid fa-flask result-card-icon";
      if (resultTitle) resultTitle.textContent = "✓ Local Simulation Completed";
      if (resultMessage) resultMessage.textContent = "[LOCAL SIMULATION] Internal pipeline executed successfully without external Meta API calls.";

      if (resultMsgId) resultMsgId.textContent = "SIMULATED (No Meta ID)";
      if (resultModeLbl) resultModeLbl.textContent = "LOCAL SIMULATION";
      if (resultTimestamp) resultTimestamp.textContent = res.sent_at ? new Date(res.sent_at).toLocaleTimeString() : new Date().toLocaleTimeString();
      if (resultProviderLbl) resultProviderLbl.textContent = "Local Simulator";
      if (resultMetaInfo) resultMetaInfo.style.display = "flex";
      if (retrySendBtn) retrySendBtn.style.display = "none";

      if (sendStatusDisplay) {
        sendStatusDisplay.innerHTML = `<span style="color: #c084fc; font-weight: 700;"><i class="fa-solid fa-flask"></i> Local simulation succeeded</span>`;
      }

    } else if (res.status === "not_eligible" || res.status === "not_messageable" || res.error_code === "RECIPIENT_NOT_ELIGIBLE") {
      sendResultCard.className = "send-result-card ineligible-card";
      if (resultIcon) resultIcon.className = "fa-solid fa-triangle-exclamation result-card-icon";
      if (resultTitle) resultTitle.textContent = "Not eligible for Instagram API messaging";
      const explanation = res.error || "This Instagram account was found, but Meta does not currently allow this account to be contacted through the connected Instagram Messaging API.";
      const reasonDetail = res.reason || res.details || "Meta's official Graph API prohibits cold direct messages by username alone. The recipient must first message your connected Instagram Business account to generate an Instagram-Scoped ID (IGSID).";
      
      const cleanUser = currentDiscoveredUsername ? currentDiscoveredUsername.replace(/^@/, '') : "creator";
      const profileUrl = `https://www.instagram.com/${cleanUser}/`;

      if (resultMessage) {
        resultMessage.innerHTML = `
          <strong>${escapeHtml(explanation)}</strong>
          <p style="margin-top: 8px; color: var(--text-secondary); font-size: 13px;">${escapeHtml(reasonDetail)}</p>
          <div style="margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap;">
            <button type="button" class="mini-action-btn primary-mini-btn" onclick="navigator.clipboard.writeText(document.getElementById('active-dispatch-textarea')?.value || document.getElementById('outreach-textarea')?.value || ''); this.innerHTML='<i class=\\\'fa-solid fa-check\\\'></i> Copied ✓'; setTimeout(() => this.innerHTML='<i class=\\\'fa-regular fa-copy\\\'></i> Copy Message', 2000);">
              <i class="fa-regular fa-copy"></i> Copy Message
            </button>
            <a href="${profileUrl}" target="_blank" rel="noopener noreferrer" class="mini-action-btn secondary-mini-btn">
              <i class="fa-solid fa-arrow-up-right-from-square"></i> Open @${escapeHtml(cleanUser)} on Instagram
            </a>
          </div>
        `;
      }
      if (retrySendBtn) retrySendBtn.style.display = "none";
      if (resultMetaInfo) resultMetaInfo.style.display = "none";

      if (sendStatusDisplay) {
        sendStatusDisplay.innerHTML = `<span style="color: #fbbf24; font-weight: 600;"><i class="fa-solid fa-triangle-exclamation"></i> Not eligible for API messaging</span>`;
      }

    } else if (res.status === "not_configured" || res.error_code === "META_NOT_CONFIGURED") {
      sendResultCard.className = "send-result-card error-card";
      if (resultIcon) resultIcon.className = "fa-solid fa-circle-xmark result-card-icon";
      if (resultTitle) resultTitle.textContent = "Configuration/authentication error";
      if (resultMessage) resultMessage.textContent = res.error || res.reason || "Meta Instagram API credentials (INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID) are not configured on the server.";
      if (retrySendBtn) retrySendBtn.style.display = "none";
      if (resultMetaInfo) resultMetaInfo.style.display = "none";

      if (sendStatusDisplay) {
        sendStatusDisplay.innerHTML = `<span style="color: #fb7185;"><i class="fa-solid fa-xmark"></i> Configuration/authentication error</span>`;
      }

    } else if (res.status === "account_unresolved" || res.error_code === "ACCOUNT_UNRESOLVED") {
      sendResultCard.className = "send-result-card error-card";
      if (resultIcon) resultIcon.className = "fa-solid fa-circle-xmark result-card-icon";
      if (resultTitle) resultTitle.textContent = "Instagram account could not be resolved";
      if (resultMessage) resultMessage.textContent = res.error || "No valid Instagram username, profile URL, or recipient ID was found.";
      if (retrySendBtn) retrySendBtn.style.display = "none";
      if (resultMetaInfo) resultMetaInfo.style.display = "none";

      if (sendStatusDisplay) {
        sendStatusDisplay.innerHTML = `<span style="color: #fb7185;"><i class="fa-solid fa-xmark"></i> Account could not be resolved</span>`;
      }

    } else {
      sendResultCard.className = "send-result-card error-card";
      if (resultIcon) resultIcon.className = "fa-solid fa-circle-xmark result-card-icon";
      if (resultTitle) resultTitle.textContent = "Meta API error";
      const errMsg = (res.error && res.error.message) ? res.error.message : (res.reason || res.message || res.error || "Meta API rejected the request.");
      if (resultMessage) {
        resultMessage.innerHTML = `
          <strong>${escapeHtml(errMsg)}</strong>
          ${res.meta_diagnostics ? `<div style="margin-top: 6px; font-size: 12px; color: var(--text-muted);">HTTP ${res.meta_diagnostics.http_status || '400'} | Code: ${res.meta_diagnostics.code || 'N/A'} | Trace: ${escapeHtml(res.meta_diagnostics.fbtrace_id || 'N/A')}</div>` : ''}
        `;
      }
      if (retrySendBtn) retrySendBtn.style.display = "inline-flex";
      if (resultMetaInfo) resultMetaInfo.style.display = "none";

      if (sendStatusDisplay) {
        sendStatusDisplay.innerHTML = `<span style="color: #fb7185;"><i class="fa-solid fa-xmark"></i> Failed: Meta API error</span>`;
      }
    }

    sendResultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function renderQuickModalSendResult(res) {
    if (!quickModalResultCard) return;
    quickModalResultCard.style.display = "block";

    if (res.status === "prepared" || res.delivery_method === "manual_instagram") {
      quickModalResultCard.className = "send-result-card success-card";
      if (quickResultIcon) quickResultIcon.className = "fa-solid fa-arrow-up-right-from-square result-card-icon";
      if (quickResultTitle) quickResultTitle.textContent = "Instagram Profile Opened";
      if (quickResultMessage) quickResultMessage.textContent = res.message || "Instagram profile opened in a new tab. Your message is copied to clipboard.";
      if (quickResultMetaInfo) quickResultMetaInfo.style.display = "none";
      return;
    }

    if (res.success && res.status === "sent") {
      quickModalResultCard.className = "send-result-card success-card";
      if (quickResultIcon) quickResultIcon.className = "fa-solid fa-circle-check result-card-icon";
      if (quickResultTitle) quickResultTitle.textContent = "✓ Message sent";
      if (quickResultMessage) {
        quickResultMessage.innerHTML = `Official Meta Graph API confirmed message delivery.<br><strong>Message ID:</strong> <code style="color: #38bdf8;">${escapeHtml(res.message_id || "N/A")}</code>`;
      }
      if (quickResultMsgId) quickResultMsgId.textContent = res.message_id || "N/A";
      if (quickResultMode) quickResultMode.textContent = "REAL META API";
      if (quickResultTimestamp) quickResultTimestamp.textContent = res.sent_at ? new Date(res.sent_at).toLocaleTimeString() : new Date().toLocaleTimeString();
      if (quickResultMetaInfo) quickResultMetaInfo.style.display = "flex";

    } else if (res.success && res.status === "simulated") {
      quickModalResultCard.className = "send-result-card success-card";
      if (quickResultIcon) quickResultIcon.className = "fa-solid fa-flask result-card-icon";
      if (quickResultTitle) quickResultTitle.textContent = "✓ Local Simulation Completed";
      if (quickResultMessage) quickResultMessage.textContent = "[LOCAL SIMULATION] Internal pipeline executed without external Meta API calls.";
      if (quickResultMsgId) quickResultMsgId.textContent = "SIMULATED";
      if (quickResultMode) quickResultMode.textContent = "LOCAL SIMULATION";
      if (quickResultTimestamp) quickResultTimestamp.textContent = res.sent_at ? new Date(res.sent_at).toLocaleTimeString() : new Date().toLocaleTimeString();
      if (quickResultMetaInfo) quickResultMetaInfo.style.display = "flex";

    } else if (res.status === "not_eligible" || res.status === "not_messageable" || res.error_code === "RECIPIENT_NOT_ELIGIBLE") {
      quickModalResultCard.className = "send-result-card ineligible-card";
      if (quickResultIcon) quickResultIcon.className = "fa-solid fa-triangle-exclamation result-card-icon";
      if (quickResultTitle) quickResultTitle.textContent = "Not eligible for Instagram API messaging";
      const cleanUser = currentDiscoveredUsername ? currentDiscoveredUsername.replace(/^@/, '') : "creator";
      const profileUrl = `https://www.instagram.com/${cleanUser}/`;
      const explanation = res.error || "This Instagram account was found, but Meta does not currently allow this account to be contacted through the connected Instagram Messaging API.";
      const reasonDetail = res.reason || res.details || "Meta's official Graph API prohibits cold direct messages by username alone. The recipient must first message your connected Instagram Business account to generate an Instagram-Scoped ID (IGSID).";

      if (quickResultMessage) {
        quickResultMessage.innerHTML = `
          <strong>${escapeHtml(explanation)}</strong>
          <p style="margin-top: 6px; color: var(--text-secondary); font-size: 13px;">${escapeHtml(reasonDetail)}</p>
          <div style="margin-top: 10px; display: flex; gap: 8px;">
            <a href="${profileUrl}" target="_blank" rel="noopener noreferrer" class="mini-action-btn secondary-mini-btn">
              <i class="fa-solid fa-arrow-up-right-from-square"></i> Open @${escapeHtml(cleanUser)} on Instagram
            </a>
          </div>
        `;
      }
      if (quickResultMetaInfo) quickResultMetaInfo.style.display = "none";

    } else if (res.status === "not_configured" || res.error_code === "META_NOT_CONFIGURED") {
      quickModalResultCard.className = "send-result-card error-card";
      if (quickResultIcon) quickResultIcon.className = "fa-solid fa-circle-xmark result-card-icon";
      if (quickResultTitle) quickResultTitle.textContent = "Configuration/authentication error";
      if (quickResultMessage) quickResultMessage.textContent = res.error || res.reason || "Meta Instagram API credentials are not configured on the server.";
      if (quickResultMetaInfo) quickResultMetaInfo.style.display = "none";

    } else if (res.status === "account_unresolved" || res.error_code === "ACCOUNT_UNRESOLVED") {
      quickModalResultCard.className = "send-result-card error-card";
      if (quickResultIcon) quickResultIcon.className = "fa-solid fa-circle-xmark result-card-icon";
      if (quickResultTitle) quickResultTitle.textContent = "Instagram account could not be resolved";
      if (quickResultMessage) quickResultMessage.textContent = res.error || "Instagram account could not be resolved from the request.";
      if (quickResultMetaInfo) quickResultMetaInfo.style.display = "none";

    } else {
      quickModalResultCard.className = "send-result-card ineligible-card";
      if (quickResultIcon) quickResultIcon.className = "fa-solid fa-triangle-exclamation result-card-icon";
      if (quickResultTitle) quickResultTitle.textContent = "Meta API error";
      const errMsg = (res.error && res.error.message) ? res.error.message : (res.reason || res.message || res.error || "Meta rejected the message or recipient is ineligible.");
      if (quickResultMessage) quickResultMessage.textContent = errMsg;
      if (quickResultMetaInfo) quickResultMetaInfo.style.display = "none";
    }

    quickModalResultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  if (retrySendBtn) {
    retrySendBtn.addEventListener("click", () => {
      if (sendInstagramBtn) sendInstagramBtn.click();
    });
  }

  // ==========================================
  // 11. Evidence Trail Table
  // ==========================================
  function renderEvidenceTrail(evidenceItems) {
    if (!evidenceTableTbody) return;
    evidenceTableTbody.innerHTML = "";
    if (!evidenceItems || evidenceItems.length === 0) {
      evidenceTableTbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No evidence items recorded.</td></tr>`;
      return;
    }

    evidenceItems.forEach(item => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><code>${escapeHtml(item.field)}</code></td>
        <td><span class="pill-badge ${item.confidence === 'High' ? 'pill-success' : 'pill-warning'}">${item.confidence}</span></td>
        <td>${escapeHtml(item.source)}</td>
        <td><div style="max-height: 80px; overflow-y: auto; font-size: 12px;">${escapeHtml(item.context || item.raw_match)}</div></td>
      `;
      evidenceTableTbody.appendChild(tr);
    });
  }

  if (viewEvidenceTrailBtn) {
    viewEvidenceTrailBtn.addEventListener("click", () => {
      if (!evidenceTrailSection) return;
      const isHidden = evidenceTrailSection.style.display === "none";
      evidenceTrailSection.style.display = isHidden ? "block" : "none";
      if (isHidden) {
        evidenceTrailSection.scrollIntoView({ behavior: "smooth" });
      }
    });
  }

  if (closeEvidenceBtn) {
    closeEvidenceBtn.addEventListener("click", () => {
      if (evidenceTrailSection) evidenceTrailSection.style.display = "none";
    });
  }

  // ==========================================
  // 12. Message History Modal
  // ==========================================
  if (viewHistoryBtn) {
    viewHistoryBtn.addEventListener("click", async () => {
      if (historyModal) historyModal.style.display = "flex";
      if (historyList) {
        historyList.innerHTML = `<div style="text-align:center; padding: 20px; color: var(--text-muted);"><i class="fa-solid fa-circle-notch fa-spin"></i> Loading message logs...</div>`;
      }

      try {
        const res = await fetch("/api/social/instagram/history");
        if (res.ok) {
          const data = await res.json();
          renderHistoryList(data);
        } else {
          if (historyList) historyList.innerHTML = `<div style="color: #fb7185;">Failed to load history.</div>`;
        }
      } catch (e) {
        if (historyList) historyList.innerHTML = `<div style="color: #fb7185;">Error loading history: ${e.message}</div>`;
      }
    });
  }

  function renderHistoryList(records) {
    if (!historyList) return;
    if (!records || records.length === 0) {
      historyList.innerHTML = `<div style="text-align: center; padding: 30px; color: var(--text-muted);">No outreach attempts recorded yet.</div>`;
      return;
    }

    historyList.innerHTML = "";
    // Show newest first
    records.slice().reverse().forEach(rec => {
      const card = document.createElement("div");
      card.className = "history-item-card";

      const isSent = rec.status === "sent";
      const isSim = rec.status === "simulated" || rec.mode === "simulation";
      const isManual = rec.delivery_method === "manual_instagram" || rec.mode === "cold_outreach" || rec.status === "prepared" || rec.status === "opened" || rec.status === "manual_action_required";
      
      let statusPillClass = "pill-danger";
      let statusLabel = "Failed";

      if (isSent) {
        statusPillClass = "pill-success";
        statusLabel = "Real Meta Sent ✓";
      } else if (isSim) {
        statusPillClass = "pill-neutral";
        statusLabel = "Simulated";
      } else if (isManual) {
        statusPillClass = "pill-warning";
        statusLabel = "Manual action required";
      } else if (rec.status === "rejected") {
        statusPillClass = "pill-warning";
        statusLabel = "Meta Rejected";
      }

      let deliveryMethodLabel = "Manual Instagram";
      if (rec.delivery_method === "meta_api" || rec.provider === "meta") {
        deliveryMethodLabel = "Meta API";
      } else if (rec.delivery_method === "simulation" || rec.provider === "local") {
        deliveryMethodLabel = "Local Simulation";
      }

      card.innerHTML = `
        <div class="history-item-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <div>
            <strong>Creator: @${escapeHtml((rec.instagram_username || "unknown").replace(/^@/, ''))}</strong>
            <span style="font-size:12px; color: var(--text-muted); margin-left: 8px;">Channel: Instagram</span>
          </div>
          <span class="pill-badge ${statusPillClass}">${statusLabel}</span>
        </div>
        <div style="font-size: 12px; color: var(--text-secondary); margin: 6px 0;">
          <strong>Method:</strong> ${escapeHtml(deliveryMethodLabel)}
          ${rec.meta_message_id ? `&nbsp;|&nbsp; <strong>Message ID:</strong> <code>${escapeHtml(rec.meta_message_id)}</code>` : ""}
          <span style="float: right; color: var(--text-muted);">${new Date(rec.sent_at || rec.prepared_at || rec.created_at).toLocaleString()}</span>
        </div>
        <div class="history-item-body" style="background: rgba(0,0,0,0.25); padding: 8px 12px; border-radius: 4px; font-size: 13px; color: var(--text-main); margin-top: 6px;">"${escapeHtml(rec.message)}"</div>
        ${rec.error ? `<div class="history-item-meta" style="color: #fb7185; margin-top: 4px;">Error: ${escapeHtml(rec.error)}</div>` : ""}
      `;
      historyList.appendChild(card);
    });
  }

  if (closeHistoryModalBtn) {
    closeHistoryModalBtn.addEventListener("click", () => {
      if (historyModal) historyModal.style.display = "none";
    });
  }

  if (historyModal) {
    historyModal.addEventListener("click", (e) => {
      if (e.target === historyModal) {
        historyModal.style.display = "none";
      }
    });
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});

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
  const regenerateOutreachBtn = document.getElementById("regenerate-outreach-btn");
  const editOutreachBtn = document.getElementById("edit-outreach-btn");
  const editBtnText = document.getElementById("edit-btn-text");
  const copyOutreachBtn = document.getElementById("copy-outreach-btn");
  const outreachTextarea = document.getElementById("outreach-textarea");
  const charCountVal = document.getElementById("char-count-val");
  const groundingEvidenceList = document.getElementById("grounding-evidence-list");

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
  let activeMessageType = "test"; // "test" or "outreach"
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
  creatorUrlInput.addEventListener("input", () => {
    clearInputBtn.style.display = creatorUrlInput.value.trim() ? "block" : "none";
  });

  clearInputBtn.addEventListener("click", () => {
    creatorUrlInput.value = "";
    clearInputBtn.style.display = "none";
    creatorUrlInput.focus();
  });

  sampleChips.forEach(chip => {
    chip.addEventListener("click", () => {
      const url = chip.getAttribute("data-url");
      if (url) {
        creatorUrlInput.value = url;
        clearInputBtn.style.display = "block";
        discoveryForm.dispatchEvent(new Event("submit"));
      }
    });
  });

  // ==========================================
  // 3. Extraction Pipeline Trigger
  // ==========================================
  discoveryForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const inputUrl = creatorUrlInput.value.trim();
    if (!inputUrl) return;

    hideError();
    startProgressAnimation();
    setSearchingState(true);
    creatorWorkspace.style.display = "none";
    evidenceTrailSection.style.display = "none";
    sendResultCard.style.display = "none";
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

  function setSearchingState(isSearching) {
    findCreatorBtn.disabled = isSearching;
    const label = findCreatorBtn.querySelector(".btn-label");
    const loading = findCreatorBtn.querySelector(".btn-loading");
    if (label) label.style.display = isSearching ? "none" : "inline-flex";
    if (loading) loading.style.display = isSearching ? "inline-flex" : "none";
  }

  // Animated Progress Pipeline
  let progressInterval = null;
  function startProgressAnimation() {
    pipelineProgress.style.display = "block";
    progressBarFill.style.width = "5%";
    
    const stages = [
      { text: "Resolving YouTube URL & channel handle...", pct: 20 },
      { text: "Fetching official YouTube metadata & descriptions...", pct: 45 },
      { text: "Extracting RFC verified business emails & social links...", pct: 70 },
      { text: "Enriching creator context with Google Gemini AI...", pct: 90 },
      { text: "Assembling verified contact intelligence...", pct: 98 }
    ];

    let stageIdx = 0;
    pipelineStatusText.textContent = stages[0].text;
    progressBarFill.style.width = stages[0].pct + "%";

    progressInterval = setInterval(() => {
      stageIdx++;
      if (stageIdx < stages.length) {
        pipelineStatusText.textContent = stages[stageIdx].text;
        progressBarFill.style.width = stages[stageIdx].pct + "%";
      }
    }, 1200);
  }

  function finishProgressAnimation() {
    if (progressInterval) clearInterval(progressInterval);
    progressBarFill.style.width = "100%";
    pipelineStatusText.textContent = "Extraction complete!";
    setTimeout(() => {
      pipelineProgress.style.display = "none";
      progressBarFill.style.width = "0%";
    }, 500);
  }

  function showError(title, msg) {
    errorTitle.textContent = title;
    errorMessage.textContent = msg;
    errorBanner.style.display = "flex";
    errorBanner.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function hideError() {
    errorBanner.style.display = "none";
  }

  dismissErrorBtn.addEventListener("click", hideError);

  // ==========================================
  // 4. Render Creator Workspace
  // ==========================================
  function renderCreatorWorkspace(data) {
    const yt = data.youtube || {};
    const emails = data.emails || [];
    const socials = data.social_links || data.social_media || {};
    const evidence = data.evidence || [];

    // 1. Profile Card
    creatorName.textContent = yt.channel_title || yt.title || "Creator Discovered";
    creatorHandle.textContent = yt.custom_url ? `@${yt.custom_url.replace(/^@/, '')}` : (yt.channel_id || "");
    
    if (yt.url) {
      creatorProfileLink.href = yt.url;
      creatorProfileLink.style.display = "inline-flex";
    } else {
      creatorProfileLink.style.display = "none";
    }

    creatorSubscribersVal.textContent = yt.subscriber_count ? formatNumber(yt.subscriber_count) : "Hidden";
    creatorViewsVal.textContent = yt.view_count ? formatNumber(yt.view_count) : "--";

    if (yt.video_title) {
      creatorRecentTitle.textContent = yt.video_title;
      metricRecentContent.style.display = "flex";
    } else {
      metricRecentContent.style.display = "none";
    }

    creatorBioText.textContent = yt.description ? yt.description.slice(0, 240) + (yt.description.length > 240 ? "..." : "") : "No public bio or description available for this account.";

    if (yt.thumbnail_url) {
      creatorAvatarImg.src = yt.thumbnail_url;
      creatorAvatarImg.style.display = "block";
      creatorAvatarFallback.style.display = "none";
    } else {
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

    creatorWorkspace.style.display = "flex";
    creatorWorkspace.scrollIntoView({ behavior: "smooth" });
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
      discoveredEmailAddress.textContent = primaryEmail.email;
      emailEvidenceText.textContent = primaryEmail.evidence
        ? `Source: ${primaryEmail.source} ("${primaryEmail.evidence.slice(0, 50)}...")`
        : `Source: ${primaryEmail.source}`;

      emailStatusPill.className = "pill-badge pill-success";
      emailStatusPill.innerHTML = `<i class="fa-solid fa-circle-check"></i> Discovered (${emails.length})`;

      emailFoundView.style.display = "block";
      emailNotFoundView.style.display = "none";
    } else {
      emailStatusPill.className = "pill-badge pill-neutral";
      emailStatusPill.textContent = "Not Found";

      emailFoundView.style.display = "none";
      emailNotFoundView.style.display = "block";
    }
  }

  copyEmailBtn.addEventListener("click", () => {
    const text = discoveredEmailAddress.textContent;
    if (text) {
      navigator.clipboard.writeText(text);
      copyEmailBtn.innerHTML = `<i class="fa-solid fa-check"></i> Copied`;
      setTimeout(() => {
        copyEmailBtn.innerHTML = `<i class="fa-regular fa-copy"></i> Copy`;
      }, 2000);
    }
  });

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
      discoveredIgUsername.textContent = handle;
      openIgLink.href = igAccount.url || `https://instagram.com/${handle}`;
      igEvidenceText.textContent = `Discovered via ${igAccount.source || 'YouTube metadata'} (${igAccount.confidence || 'High'} Confidence)`;

      igDiscoveryPill.className = "pill-badge pill-success";
      igDiscoveryPill.innerHTML = `<i class="fa-solid fa-circle-check"></i> Discovered`;

      igFoundView.style.display = "block";
      igNotFoundView.style.display = "none";

      consoleDiscoveryVal.textContent = `@${handle}`;
      consoleDiscoveryVal.className = "console-meta-value highlight-ig";
    } else {
      currentDiscoveredUsername = null;
      igDiscoveryPill.className = "pill-badge pill-neutral";
      igDiscoveryPill.textContent = "Not Found";

      igFoundView.style.display = "none";
      igNotFoundView.style.display = "block";

      consoleDiscoveryVal.textContent = "Not Discovered";
      consoleDiscoveryVal.className = "console-meta-value text-muted";
    }
  }

  // ==========================================
  // 7. Other Social Media Accordion
  // ==========================================
  function renderOtherSocials(socials) {
    const otherKeys = Object.keys(socials).filter(k => k !== "instagram");
    if (otherKeys.length > 0) {
      otherSocialsCount.textContent = otherKeys.length;
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

      otherSocialsCard.style.display = "block";
    } else {
      otherSocialsCard.style.display = "none";
    }
  }

  toggleOtherSocials.addEventListener("click", () => {
    const isOpen = otherSocialsContent.style.display === "block";
    otherSocialsContent.style.display = isOpen ? "none" : "block";
    toggleOtherSocials.classList.toggle("open", !isOpen);
  });

  // ==========================================
  // 8. AI Outreach Generator
  // ==========================================
  async function generateAiOutreach(data) {
    const yt = data.youtube || {};
    regenerateOutreachBtn.disabled = true;
    const rotateIcon = regenerateOutreachBtn.querySelector("i");
    if (rotateIcon) rotateIcon.classList.add("fa-spin");

    try {
      const payload = {
        creator_name: yt.channel_title || "Creator",
        channel_name: yt.channel_title || "YouTube Channel",
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
        outreachTextarea.value = outreach.message || "";
        updateCharCount();

        groundingEvidenceList.innerHTML = "";
        (outreach.grounded_evidence || []).forEach(item => {
          const pill = document.createElement("span");
          pill.className = "grounding-pill";
          pill.innerHTML = `<i class="fa-solid fa-check"></i> ${escapeHtml(item)}`;
          groundingEvidenceList.appendChild(pill);
        });

        if (activeMessageType === "outreach") {
          activeDispatchTextarea.value = outreachTextarea.value;
        }
      }
    } catch (e) {
      console.warn("Outreach generation failed:", e);
    } finally {
      regenerateOutreachBtn.disabled = false;
      if (rotateIcon) rotateIcon.classList.remove("fa-spin");
    }
  }

  regenerateOutreachBtn.addEventListener("click", () => {
    if (currentExtraction) generateAiOutreach(currentExtraction);
  });

  editOutreachBtn.addEventListener("click", () => {
    isEditingOutreach = !isEditingOutreach;
    if (isEditingOutreach) {
      outreachTextarea.focus();
      editBtnText.textContent = "Done";
      editOutreachBtn.classList.add("active-edit");
    } else {
      editBtnText.textContent = "Edit";
      editOutreachBtn.classList.remove("active-edit");
    }
  });

  copyOutreachBtn.addEventListener("click", () => {
    const text = outreachTextarea.value;
    if (text) {
      navigator.clipboard.writeText(text);
      const span = copyOutreachBtn.querySelector("span");
      if (span) span.textContent = "Copied ✓";
      setTimeout(() => { if (span) span.textContent = "Copy"; }, 2000);
    }
  });

  if (useEmailOutreachBtn) {
    useEmailOutreachBtn.addEventListener("click", () => {
      const text = outreachTextarea.value;
      if (text) {
        navigator.clipboard.writeText(text);
        useEmailOutreachBtn.innerHTML = `<i class="fa-solid fa-check"></i> Outreach Copied to Clipboard!`;
        setTimeout(() => {
          useEmailOutreachBtn.innerHTML = `<i class="fa-solid fa-copy"></i> Copy Outreach for Email`;
        }, 2500);
      }
    });
  }

  outreachTextarea.addEventListener("input", updateCharCount);

  function updateCharCount() {
    charCountVal.textContent = outreachTextarea.value.length;
    if (activeMessageType === "outreach") {
      activeDispatchTextarea.value = outreachTextarea.value;
    }
  }

  // ==========================================
  // 9. Instagram Messaging Capability & Eligibility
  // ==========================================
  function getCreatorMessagingMode() {
    if (activeGlobalMode === "simulation") {
      return "simulation";
    }
    // Only "meta" if current eligibility explicitly confirms an active connected Meta conversation with resolved IGSID
    const isEligibleMeta = Boolean(
      currentEligibility && (
        (currentEligibility.messaging && currentEligibility.messaging.eligible === true) ||
        (currentEligibility.can_send === true && currentEligibility.recipient && currentEligibility.recipient.status === "resolved")
      )
    );
    return isEligibleMeta ? "meta" : "cold";
  }

  async function checkInstagramEligibility(username, user_id) {
    messagingEligibilityPill.className = "eligibility-status-pill pill-neutral";
    messagingEligibilityPill.innerHTML = `<span class="pill-dot"></span> Checking Status...`;

    if (quickModalStatusBadge) {
      quickModalStatusBadge.className = "pill-badge pill-neutral";
      quickModalStatusBadge.textContent = "Checking...";
      quickModalStatusExplanation.textContent = "Checking creator outreach readiness...";
    }

    try {
      const creatorId = currentExtraction?.channel_id || currentExtraction?.creator_id || "";
      const queryParams = new URLSearchParams({
        instagram_username: username || "",
        creator_id: creatorId,
        mode: activeGlobalMode
      });

      const res = await fetch(`/api/instagram/recipient-status?${queryParams.toString()}`);
      if (res.ok) {
        const data = await res.json();
        currentEligibility = data;
        renderEligibilityUI(data);
        renderQuickModalEligibilityUI(data);
      } else {
        const fallback = {
          mode: activeGlobalMode,
          discovery: { status: "discovered", username: username },
          messaging: { eligible: false, status: "interaction_required", reason: "Outreach ready" }
        };
        currentEligibility = fallback;
        renderEligibilityUI(fallback);
        renderQuickModalEligibilityUI(fallback);
      }
    } catch (e) {
      const fallback = {
        mode: activeGlobalMode,
        discovery: { status: "discovered", username: username },
        messaging: { eligible: false, status: "interaction_required", reason: "Outreach ready" }
      };
      currentEligibility = fallback;
      renderEligibilityUI(fallback);
      renderQuickModalEligibilityUI(fallback);
    }
  }

  function renderEligibilityUI(data) {
    const discovery = data.discovery || { username: data.instagram_username ? data.instagram_username.replace(/^@/, '') : currentDiscoveredUsername };
    const messaging = data.messaging || {};
    const canSend = Boolean(messaging.eligible || data.can_send);

    // 1. Console Meta Fields
    consoleDiscoveryVal.textContent = discovery.username ? `@${discovery.username}` : (currentDiscoveredUsername ? `@${currentDiscoveredUsername}` : "Not Discovered");
    consoleDiscoveryVal.className = (discovery.username || currentDiscoveredUsername) ? "console-meta-value highlight-ig" : "console-meta-value text-muted";

    // 2. Messaging Mode Handling
    if (messaging.eligible && canSend && activeGlobalMode === "real") {
      messagingEligibilityPill.className = "eligibility-status-pill eligible";
      messagingEligibilityPill.innerHTML = `<span class="pill-dot"></span> Meta Messaging Available`;

      eligibilityBanner.className = "eligibility-banner eligible-mode";
      eligibilityBannerIcon.className = "fa-solid fa-circle-check banner-status-icon";
      eligibilityBannerTitle.textContent = "✓ Meta Messaging Available (Connected Conversation Active)";
      eligibilityBannerDesc.textContent = messaging.reason || "Official Meta Graph API messaging is ready for direct dispatch.";

      consoleRecipientVal.textContent = "Meta Conversation Active";
      consoleRecipientVal.className = "console-meta-value highlight-ig";
      consoleCapabilityVal.textContent = "Official API Send";
      consoleCapabilityVal.className = "console-meta-value highlight-ig";

      sendInstagramBtn.disabled = false;
      sendBtnMainLabel.innerHTML = `<i class="fa-brands fa-instagram"></i> Send`;
      sendStatusDisplay.innerHTML = `<span style="color: #34d399;"><i class="fa-solid fa-check"></i> Connected conversation ready for Meta send</span>`;
      altOutreachBanner.style.display = "none";

      igCardCapabilityBadge.className = "pill-badge pill-success";
      igCardCapabilityBadge.textContent = "Meta messaging available";
      igCardCapabilityHint.textContent = "Legitimate Meta messaging identity is active for official API dispatch.";
      if (quickSendBtnLabel) quickSendBtnLabel.textContent = "Send Message";

    } else if (currentDiscoveredUsername || discovery.username) {
      const igHandle = currentDiscoveredUsername || discovery.username;
      messagingEligibilityPill.className = "eligibility-status-pill pill-warning";
      messagingEligibilityPill.innerHTML = `<span class="pill-dot"></span> Meta Interaction Required`;

      eligibilityBanner.className = "eligibility-banner warning-mode";
      eligibilityBannerIcon.className = "fa-brands fa-instagram banner-status-icon";
      eligibilityBannerTitle.textContent = `Discovered Instagram Account (@${igHandle})`;
      eligibilityBannerDesc.textContent = "Meta Graph API requires prior recipient interaction (IGSID) before direct delivery. Click Send to attempt automated send.";

      consoleRecipientVal.textContent = `@${igHandle}`;
      consoleRecipientVal.className = "console-meta-value highlight-ig";
      consoleCapabilityVal.textContent = "Meta API Send (IGSID Required)";
      consoleCapabilityVal.className = "console-meta-value highlight-ig";

      sendInstagramBtn.disabled = false;
      sendBtnMainLabel.innerHTML = `<i class="fa-brands fa-instagram"></i> Send`;
      sendStatusDisplay.innerHTML = `<span style="color: #94a3b8;"><i class="fa-solid fa-paper-plane"></i> Ready to send</span>`;
      altOutreachBanner.style.display = "none";

      igCardCapabilityBadge.className = "pill-badge pill-neutral";
      igCardCapabilityBadge.textContent = "Meta Send API";
      igCardCapabilityHint.textContent = "Click Send to attempt automated message delivery via Meta API.";
      if (quickSendBtnLabel) quickSendBtnLabel.textContent = "Send Message";

    } else {
      messagingEligibilityPill.className = "eligibility-status-pill pill-neutral";
      messagingEligibilityPill.innerHTML = `<span class="pill-dot"></span> Not Discovered`;

      eligibilityBanner.className = "eligibility-banner info-mode";
      eligibilityBannerIcon.className = "fa-solid fa-circle-info banner-status-icon";
      eligibilityBannerTitle.textContent = "No Instagram Profile Discovered";
      eligibilityBannerDesc.textContent = "An Instagram handle must be identified before outreach can be prepared.";

      consoleCapabilityVal.textContent = "None";
      sendInstagramBtn.disabled = true;
      sendBtnMainLabel.innerHTML = `<i class="fa-brands fa-instagram"></i> Send`;
      sendStatusDisplay.textContent = "No Instagram recipient found";
      altOutreachBanner.style.display = "none";

      igCardCapabilityBadge.className = "pill-badge pill-neutral";
      igCardCapabilityBadge.textContent = "Not Discovered";
      igCardCapabilityHint.textContent = "No Instagram profile discovered.";
      if (quickSendBtnLabel) quickSendBtnLabel.textContent = "Send Message";
    }
  }

  function renderQuickModalEligibilityUI(data) {
    if (!quickSendModal) return;

    const username = data.instagram_username ? data.instagram_username.replace(/^@/, '') : currentDiscoveredUsername;
    const messaging = data.messaging || {};
    const isMeta = Boolean(messaging.eligible && activeGlobalMode === "real");

    if (quickModalRecipientUsername) {
      quickModalRecipientUsername.textContent = username ? `@${username}` : "None";
    }

    if (isMeta) {
      quickModalEligibilityBox.className = "quick-eligibility-box eligible";
      quickModalStatusBadge.className = "pill-badge pill-success";
      quickModalStatusBadge.innerHTML = `<i class="fa-solid fa-circle-check"></i> Meta messaging available`;
      quickModalStatusExplanation.textContent = messaging.reason || "Legitimate Meta messaging identity is active and ready for dispatch.";
      quickModalSendBtn.style.display = "inline-flex";
      quickModalSendBtn.disabled = false;
      quickSendModalBtnText.innerHTML = `<i class="fa-brands fa-instagram"></i> Send`;

    } else {
      quickModalEligibilityBox.className = "quick-eligibility-box checking";
      quickModalStatusBadge.className = "pill-badge pill-neutral";
      quickModalStatusBadge.innerHTML = `<i class="fa-brands fa-instagram"></i> Meta Send API`;
      quickModalStatusExplanation.innerHTML = `Click <strong>"Send"</strong> to attempt automated message delivery through Meta's official API.`;
      quickModalSendBtn.style.display = "inline-flex";
      quickModalSendBtn.disabled = false;
      quickSendModalBtnText.innerHTML = `<i class="fa-brands fa-instagram"></i> Send`;
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
      quickModalRecipientUsername.textContent = `@${currentDiscoveredUsername}`;
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

    quickSendModal.style.display = "flex";
    setTimeout(() => {
      quickModalTextarea.focus();
    }, 100);
  }

  function closeInstagramTestMessageDialog() {
    quickSendModal.style.display = "none";
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
      const text = quickModalTextarea.value;
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
      metaRulesModal.style.display = "flex";
    });
  }

  if (closeMetaRulesBtn) {
    closeMetaRulesBtn.addEventListener("click", () => {
      metaRulesModal.style.display = "none";
    });
  }

  if (dismissMetaRulesBtn) {
    dismissMetaRulesBtn.addEventListener("click", () => {
      metaRulesModal.style.display = "none";
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
  tabTestMsg.addEventListener("click", () => {
    activeMessageType = "test";
    tabTestMsg.classList.add("active");
    tabAiMsg.classList.remove("active");
    activeMsgTypeLabel.textContent = "Fixed Test DM";
    activeDispatchTextarea.value = DEFAULT_TEST_MESSAGE;
  });

  tabAiMsg.addEventListener("click", () => {
    activeMessageType = "outreach";
    tabAiMsg.classList.add("active");
    tabTestMsg.classList.remove("active");
    activeMsgTypeLabel.textContent = "Customized AI Outreach";
    activeDispatchTextarea.value = outreachTextarea.value;
  });

  // Optional Recipient Drawer Toggle (if present)
  if (toggleRecipientIdBtn && recipientIdDrawer) {
    toggleRecipientIdBtn.addEventListener("click", () => {
      const isHidden = recipientIdDrawer.style.display === "none";
      recipientIdDrawer.style.display = isHidden ? "block" : "none";
    });
  }

  if (applyIgsidBtn && customIgsidInput) {
    applyIgsidBtn.addEventListener("click", () => {
      const customId = customIgsidInput.value.trim();
      if (customId) {
        activeRecipientIgsid = customId;
        applyIgsidBtn.textContent = "Applied ✓";
        checkInstagramEligibility(currentDiscoveredUsername, activeRecipientIgsid);
        setTimeout(() => { applyIgsidBtn.textContent = "Apply IGSID"; }, 2000);
      } else {
        activeRecipientIgsid = null;
        checkInstagramEligibility(currentDiscoveredUsername, null);
      }
    });
  }

  // ==========================================
  // 10. Automated Instagram API Send Action
  // ==========================================
  async function executeInstagramSend(msgToSend, triggerSource = "console") {
    if (isSendingActive) return; // Prevent double-clicks / concurrent requests
    const cleanMsg = (msgToSend || "").trim();
    if (!cleanMsg) {
      alert("Please provide a message text before sending.");
      return;
    }

    // Always attempt direct automated API send via backend
    await executeOfficialMetaSend(cleanMsg, triggerSource);
  }

  // ==========================================
  // Official Meta API Send
  // ==========================================
  async function executeOfficialMetaSend(cleanMsg, triggerSource = "modal") {
    isSendingActive = true;
    setSendingState(true, "Sending...");
    setQuickModalSendingState(true);

    sendResultCard.style.display = "none";
    resultMetaInfo.style.display = "none";
    if (quickModalResultCard) quickModalResultCard.style.display = "none";

    const cleanUser = currentDiscoveredUsername ? currentDiscoveredUsername.replace(/^@/, "").trim() : null;
    const payload = {
      creator_id: currentExtraction?.channel_id || currentExtraction?.creator_id || null,
      message: cleanMsg,
      creator_username: cleanUser,
      creator_url: cleanUser ? `https://instagram.com/${cleanUser}` : null
    };
    if (activeRecipientIgsid) {
      payload.recipient_igsid = activeRecipientIgsid;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    try {
      const response = await fetch("/api/instagram/send-message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      const result = await response.json();
      isSendingActive = false;
      setSendingState(false);
      setQuickModalSendingState(false);

      renderSendResult(result);
      renderQuickModalSendResult(result);

    } catch (err) {
      clearTimeout(timeoutId);
      isSendingActive = false;
      setSendingState(false);
      setQuickModalSendingState(false);

      const errResult = {
        success: false,
        status: "failed",
        provider: "meta_instagram",
        error: { message: err.name === "AbortError" ? "Request timed out contacting Meta API." : `Network error: ${err.message}` }
      };
      renderSendResult(errResult);
      renderQuickModalSendResult(errResult);
    }
  }

  sendInstagramBtn.addEventListener("click", () => {
    executeInstagramSend(activeDispatchTextarea.value, "console");
  });

  if (quickModalSendBtn) {
    quickModalSendBtn.addEventListener("click", () => {
      executeInstagramSend(quickModalTextarea.value, "modal");
    });
  }

  // Dedicated Copy Buttons Handlers
  if (cardCopyMsgBtn) {
    cardCopyMsgBtn.addEventListener("click", () => {
      const text = (outreachTextarea && outreachTextarea.value.trim()) || DEFAULT_TEST_MESSAGE;
      navigator.clipboard.writeText(text).then(() => {
        cardCopyMsgBtn.innerHTML = `<i class="fa-solid fa-check"></i> <span>Copied ✓</span>`;
        setTimeout(() => {
          cardCopyMsgBtn.innerHTML = `<i class="fa-regular fa-copy"></i> <span>Copy Message</span>`;
        }, 2000);
      });
    });
  }

  if (consoleCopyMsgBtn) {
    consoleCopyMsgBtn.addEventListener("click", () => {
      const text = activeDispatchTextarea.value.trim() || DEFAULT_TEST_MESSAGE;
      navigator.clipboard.writeText(text).then(() => {
        consoleCopyMsgBtn.innerHTML = `<i class="fa-solid fa-check"></i> Copied ✓`;
        setTimeout(() => {
          consoleCopyMsgBtn.innerHTML = `<i class="fa-regular fa-copy"></i> Copy Message`;
        }, 2000);
      });
    });
  }

  function setSendingState(isSending, statusMsg = "") {
    sendInstagramBtn.disabled = isSending;
    const btnText = sendInstagramBtn.querySelector(".btn-text");
    const btnSpinner = sendInstagramBtn.querySelector(".btn-spinner");
    if (btnText) btnText.style.display = isSending ? "none" : "inline-flex";
    if (btnSpinner) btnSpinner.style.display = isSending ? "inline-flex" : "none";
    if (isSending) {
      sendStatusDisplay.innerHTML = `<span style="color: #818cf8;"><i class="fa-solid fa-circle-notch fa-spin"></i> ${statusMsg || "Sending..."}</span>`;
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
    sendResultCard.style.display = "block";

    if (res.success && res.status === "sent") {
      sendResultCard.className = "send-result-card success-card";
      resultIcon.className = "fa-solid fa-circle-check result-card-icon";
      resultTitle.textContent = "✓ Message sent";
      resultMessage.textContent = "Official Meta Graph API confirmed message delivery to the recipient.";
      
      resultMsgId.textContent = res.message_id || "N/A";
      resultModeLbl.textContent = "REAL META API";
      resultTimestamp.textContent = res.sent_at ? new Date(res.sent_at).toLocaleTimeString() : new Date().toLocaleTimeString();
      resultProviderLbl.textContent = "Meta Graph API";
      resultMetaInfo.style.display = "flex";

      sendStatusDisplay.innerHTML = `<span style="color: #34d399; font-weight: 700;"><i class="fa-solid fa-check"></i> Message sent</span>`;

    } else if (res.success && res.status === "simulated") {
      sendResultCard.className = "send-result-card success-card";
      resultIcon.className = "fa-solid fa-flask result-card-icon";
      resultTitle.textContent = "✓ Local Simulation Completed";
      resultMessage.textContent = "[LOCAL SIMULATION] Internal pipeline executed successfully without external Meta API calls.";

      resultMsgId.textContent = "SIMULATED (No Meta ID)";
      resultModeLbl.textContent = "LOCAL SIMULATION";
      resultTimestamp.textContent = res.sent_at ? new Date(res.sent_at).toLocaleTimeString() : new Date().toLocaleTimeString();
      resultProviderLbl.textContent = "Local Simulator";
      resultMetaInfo.style.display = "flex";

      sendStatusDisplay.innerHTML = `<span style="color: #c084fc; font-weight: 700;"><i class="fa-solid fa-flask"></i> Local simulation succeeded</span>`;

    } else if (res.status === "not_messageable" || res.error_code === "RECIPIENT_NOT_ELIGIBLE") {
      sendResultCard.className = "send-result-card ineligible-card";
      resultIcon.className = "fa-solid fa-triangle-exclamation result-card-icon";
      resultTitle.textContent = "Unable to send automatically: recipient is not eligible for Meta messaging.";
      
      const cleanUser = currentDiscoveredUsername ? currentDiscoveredUsername.replace(/^@/, '') : 'creator';
      resultMessage.innerHTML = `${escapeHtml(res.details || res.message || "")}<br><br><strong>Meta Limitation:</strong> Meta's official Instagram Messaging Graph API does not permit initiating cold conversations to arbitrary public usernames. A recipient must first initiate a conversation with your connected Instagram Professional account (generating an Instagram-Scoped ID / IGSID) before direct messages can be delivered via the API.`;
      retrySendBtn.style.display = "none";
      resultMetaInfo.style.display = "none";

      sendStatusDisplay.innerHTML = `<span style="color: #fbbf24; font-weight: 600;"><i class="fa-solid fa-triangle-exclamation"></i> Unable to send automatically: recipient is not eligible for Meta messaging.</span>`;

    } else if (res.status === "not_configured") {
      sendResultCard.className = "send-result-card error-card";
      resultIcon.className = "fa-solid fa-circle-xmark result-card-icon";
      resultTitle.textContent = "✕ Meta Instagram API Not Configured";
      resultMessage.textContent = res.error || "Instagram messaging credentials are not configured on the server.";
      retrySendBtn.style.display = "none";
      resultMetaInfo.style.display = "none";

      sendStatusDisplay.innerHTML = `<span style="color: #fb7185;"><i class="fa-solid fa-xmark"></i> Meta API unconfigured</span>`;

    } else {
      sendResultCard.className = "send-result-card error-card";
      resultIcon.className = "fa-solid fa-circle-xmark result-card-icon";
      resultTitle.textContent = "Meta rejected this message";
      const errMsg = (res.error && res.error.message) ? res.error.message : (res.message || res.error || "Meta rejected the message or a connection error occurred.");
      resultMessage.textContent = errMsg;
      retrySendBtn.style.display = "inline-flex";
      resultMetaInfo.style.display = "none";

      sendStatusDisplay.innerHTML = `<span style="color: #fb7185;"><i class="fa-solid fa-xmark"></i> Message dispatch failed</span>`;
    }

    sendResultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function renderQuickModalSendResult(res) {
    if (!quickModalResultCard) return;
    quickModalResultCard.style.display = "block";

    if (res.success && res.status === "sent") {
      quickModalResultCard.className = "send-result-card success-card";
      quickResultIcon.className = "fa-solid fa-circle-check result-card-icon";
      quickResultTitle.textContent = "✓ Message sent";
      quickResultMessage.innerHTML = `Official Meta Graph API confirmed message delivery.<br><strong>Message ID:</strong> <code style="color: #38bdf8;">${escapeHtml(res.message_id || "N/A")}</code>`;
      quickResultMsgId.textContent = res.message_id || "N/A";
      quickResultMode.textContent = "REAL META API";
      quickResultTimestamp.textContent = res.sent_at ? new Date(res.sent_at).toLocaleTimeString() : new Date().toLocaleTimeString();
      quickResultMetaInfo.style.display = "flex";

    } else if (res.success && res.status === "simulated") {
      quickModalResultCard.className = "send-result-card success-card";
      quickResultIcon.className = "fa-solid fa-flask result-card-icon";
      quickResultTitle.textContent = "✓ Local Simulation Completed";
      quickResultMessage.textContent = "[LOCAL SIMULATION] Internal pipeline executed without external Meta API calls.";
      quickResultMsgId.textContent = "SIMULATED";
      quickResultMode.textContent = "LOCAL SIMULATION";
      quickResultTimestamp.textContent = res.sent_at ? new Date(res.sent_at).toLocaleTimeString() : new Date().toLocaleTimeString();
      quickResultMetaInfo.style.display = "flex";

    } else if (res.status === "not_messageable" || res.error_code === "RECIPIENT_NOT_ELIGIBLE") {
      quickModalResultCard.className = "send-result-card ineligible-card";
      quickResultIcon.className = "fa-solid fa-triangle-exclamation result-card-icon";
      quickResultTitle.textContent = "Unable to send automatically: recipient is not eligible for Meta messaging.";
      quickResultMessage.innerHTML = `${escapeHtml(res.details || res.message || "")}<br><br><strong>Meta Limitation:</strong> Meta's official Instagram Messaging Graph API does not permit initiating cold conversations to arbitrary public usernames. A recipient must first initiate a conversation with your connected Instagram Professional account (generating an Instagram-Scoped ID / IGSID) before direct messages can be delivered via the API.`;
      quickResultMetaInfo.style.display = "none";

    } else {
      quickModalResultCard.className = "send-result-card ineligible-card";
      quickResultIcon.className = "fa-solid fa-triangle-exclamation result-card-icon";
      quickResultTitle.textContent = "Meta rejected this message";
      const errMsg = (res.error && res.error.message) ? res.error.message : (res.message || res.error || "Meta rejected the message or recipient is ineligible.");
      quickResultMessage.textContent = errMsg;
      quickResultMetaInfo.style.display = "none";
    }

    quickModalResultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  retrySendBtn.addEventListener("click", () => {
    sendInstagramBtn.click();
  });

  // ==========================================
  // 11. Evidence Trail Table
  // ==========================================
  function renderEvidenceTrail(evidenceItems) {
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

  viewEvidenceTrailBtn.addEventListener("click", () => {
    const isHidden = evidenceTrailSection.style.display === "none";
    evidenceTrailSection.style.display = isHidden ? "block" : "none";
    if (isHidden) {
      evidenceTrailSection.scrollIntoView({ behavior: "smooth" });
    }
  });

  closeEvidenceBtn.addEventListener("click", () => {
    evidenceTrailSection.style.display = "none";
  });

  // ==========================================
  // 12. Message History Modal
  // ==========================================
  viewHistoryBtn.addEventListener("click", async () => {
    historyModal.style.display = "flex";
    historyList.innerHTML = `<div style="text-align:center; padding: 20px; color: var(--text-muted);"><i class="fa-solid fa-circle-notch fa-spin"></i> Loading message logs...</div>`;

    try {
      const res = await fetch("/api/social/instagram/history");
      if (res.ok) {
        const data = await res.json();
        renderHistoryList(data);
      } else {
        historyList.innerHTML = `<div style="color: #fb7185;">Failed to load history.</div>`;
      }
    } catch (e) {
      historyList.innerHTML = `<div style="color: #fb7185;">Error loading history: ${e.message}</div>`;
    }
  });

  function renderHistoryList(records) {
    if (!records || records.length === 0) {
      historyList.innerHTML = `<div style="text-align: center; padding: 30px; color: var(--text-muted);">No Instagram messages have been recorded yet.</div>`;
      return;
    }

    historyList.innerHTML = "";
    // Show newest first
    records.slice().reverse().forEach(rec => {
      const card = document.createElement("div");
      card.className = "history-item-card";

      const isSent = rec.status === "sent";
      const isSim = rec.status === "simulated" || rec.mode === "simulation";
      
      let statusPillClass = "pill-danger";
      let statusLabel = "Failed";

      if (isSent) {
        statusPillClass = "pill-success";
        statusLabel = "Real Meta Sent ✓";
      } else if (isSim) {
        statusPillClass = "pill-neutral";
        statusLabel = "Simulated";
      } else if (rec.status === "rejected") {
        statusPillClass = "pill-warning";
        statusLabel = "Meta Rejected";
      }

      card.innerHTML = `
        <div class="history-item-header">
          <div>
            <strong>To: @${escapeHtml(rec.instagram_username || "unknown")}</strong>
            ${rec.meta_recipient_id ? `<span style="font-size:11px; color: var(--text-muted);"> (ID: ${rec.meta_recipient_id})</span>` : ""}
          </div>
          <span class="pill-badge ${statusPillClass}">${statusLabel}</span>
        </div>
        <div class="history-item-body">"${escapeHtml(rec.message)}"</div>
        <div class="history-item-meta">
          <span>Mode: ${rec.mode || "real"}</span>
          <span>Type: ${rec.message_type}</span>
          <span>Time: ${new Date(rec.created_at).toLocaleString()}</span>
          ${rec.meta_message_id ? `<span>Meta ID: ${rec.meta_message_id}</span>` : ""}
          ${rec.error ? `<span style="color: #fb7185;">Error: ${escapeHtml(rec.error)}</span>` : ""}
        </div>
      `;
      historyList.appendChild(card);
    });
  }

  closeHistoryModalBtn.addEventListener("click", () => {
    historyModal.style.display = "none";
  });

  historyModal.addEventListener("click", (e) => {
    if (e.target === historyModal) {
      historyModal.style.display = "none";
    }
  });

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

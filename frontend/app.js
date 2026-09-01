/**
 * Creator Discovery & AI Outreach Application Logic
 * Integrates FastAPI Intelligence, Gemini Outreach, and Official Meta Instagram Messaging
 */

document.addEventListener("DOMContentLoaded", () => {
  // Elements - Navigation & Health
  const statusYt = document.getElementById("status-yt");
  const statusGemini = document.getElementById("status-gemini");
  const statusMeta = document.getElementById("status-meta");

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

  const consoleDiscoveryVal = document.getElementById("console-discovery-val");
  const consoleRecipientVal = document.getElementById("console-recipient-val");
  const consoleApiStatusVal = document.getElementById("console-api-status-val");

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
  const sendResultCard = document.getElementById("send-result-card");
  const resultIcon = document.getElementById("result-icon");
  const resultTitle = document.getElementById("result-title");
  const resultMessage = document.getElementById("result-message");
  const resultMetaInfo = document.getElementById("result-meta-info");
  const resultMsgId = document.getElementById("result-msg-id");
  const resultTimestamp = document.getElementById("result-timestamp");
  const retrySendBtn = document.getElementById("retry-send-btn");

  // Elements - Evidence Trail & Modals
  const evidenceTrailSection = document.getElementById("evidence-trail-section");
  const closeEvidenceBtn = document.getElementById("close-evidence-btn");
  const evidenceTableTbody = document.getElementById("evidence-table-tbody");
  const historyModal = document.getElementById("history-modal");
  const closeHistoryModalBtn = document.getElementById("close-history-modal-btn");
  const historyList = document.getElementById("history-list");

  // State
  let currentExtraction = null;
  let currentDiscoveredUsername = null;
  let activeRecipientIgsid = null;
  let currentEligibility = null;
  let isEditingOutreach = false;
  let activeMessageType = "test"; // "test" or "outreach"

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
  // 1. Initial Health Check
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
      creatorUrlInput.value = chip.dataset.url;
      clearInputBtn.style.display = "block";
      creatorUrlInput.focus();
    });
  });

  dismissErrorBtn.addEventListener("click", () => {
    errorBanner.style.display = "none";
  });

  function showError(title, msg) {
    errorTitle.textContent = title;
    errorMessage.textContent = msg;
    errorBanner.style.display = "flex";
    errorBanner.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function hideError() {
    errorBanner.style.display = "none";
  }

  // ==========================================
  // 3. Creator Discovery Submission
  // ==========================================
  discoveryForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const url = creatorUrlInput.value.trim();
    if (!url) return;

    hideError();
    creatorWorkspace.style.display = "none";
    pipelineProgress.style.display = "block";
    setDiscoveryLoading(true);

    // Simulated progress stage transitions
    let progressStep = 1;
    updateProgressUI(1, "Validating and resolving input URL...");

    const progressTimer = setInterval(() => {
      if (progressStep < 4) {
        progressStep++;
        const msgs = [
          "Parsing URL and identifier...",
          "Retrieving official YouTube channel metadata & profile...",
          "Extracting verified emails and detecting social handles...",
          "Validating Instagram profile and checking Meta eligibility..."
        ];
        updateProgressUI(progressStep, msgs[progressStep - 1]);
      }
    }, 450);

    try {
      const response = await fetch("/api/extract", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url })
      });

      clearInterval(progressTimer);
      const result = await response.json();

      if (!result.success || !result.data) {
        pipelineProgress.style.display = "none";
        setDiscoveryLoading(false);
        showError("Creator Discovery Failed", result.error || "Could not find a valid creator from the provided link.");
        return;
      }

      updateProgressUI(5, "Generating AI outreach and finalizing intelligence...");
      
      setTimeout(async () => {
        pipelineProgress.style.display = "none";
        currentExtraction = result.data;
        renderCreatorWorkspace(result.data);
        setDiscoveryLoading(false);
      }, 400);

    } catch (err) {
      clearInterval(progressTimer);
      pipelineProgress.style.display = "none";
      setDiscoveryLoading(false);
      showError("Connection Error", `Failed to reach server: ${err.message}`);
    }
  });

  function setDiscoveryLoading(isLoading) {
    findCreatorBtn.disabled = isLoading;
    const btnLabel = findCreatorBtn.querySelector(".btn-label");
    const btnLoading = findCreatorBtn.querySelector(".btn-loading");
    if (btnLabel) btnLabel.style.display = isLoading ? "none" : "inline-flex";
    if (btnLoading) btnLoading.style.display = isLoading ? "inline-flex" : "none";
  }

  function updateProgressUI(step, text) {
    pipelineStatusText.textContent = text;
    const percent = Math.min(step * 20, 100);
    progressBarFill.style.width = `${percent}%`;

    for (let s = 1; s <= 5; s++) {
      const el = document.getElementById(`p-step-${s}`);
      if (el) {
        if (s < step) {
          el.className = "step-badge completed";
          el.innerHTML = `<i class="fa-solid fa-check"></i> ${el.textContent.trim()}`;
        } else if (s === step) {
          el.className = "step-badge active";
        } else {
          el.className = "step-badge";
        }
      }
    }
  }

  // ==========================================
  // 4. Render Creator Workspace
  // ==========================================
  async function renderCreatorWorkspace(data) {
    const yt = data.youtube || {};
    const emails = data.emails || [];
    const socials = data.social_media || {};
    const evidence = data.evidence || [];

    // 1. Profile Information
    creatorName.textContent = yt.channel_name || "Discovered Creator";
    const channelId = yt.channel_id || "";
    creatorHandle.textContent = channelId ? `@${channelId}` : "@creator";
    creatorProfileLink.href = yt.channel_url || yt.video_url || "#";

    // Avatar
    if (yt.avatar_url) {
      creatorAvatarImg.src = yt.avatar_url;
      creatorAvatarImg.style.display = "block";
      creatorAvatarFallback.style.display = "none";
    } else {
      creatorAvatarImg.style.display = "none";
      creatorAvatarFallback.style.display = "flex";
    }

    // Stats
    if (yt.subscriber_count !== null && yt.subscriber_count !== undefined) {
      creatorSubscribersVal.textContent = Number(yt.subscriber_count).toLocaleString();
    } else {
      creatorSubscribersVal.textContent = "N/A";
    }

    if (yt.view_count !== null && yt.view_count !== undefined) {
      creatorViewsVal.textContent = Number(yt.view_count).toLocaleString();
    } else {
      creatorViewsVal.textContent = "N/A";
    }

    if (yt.video_title) {
      creatorRecentTitle.textContent = yt.video_title;
      metricRecentContent.style.display = "flex";
    } else {
      metricRecentContent.style.display = "none";
    }

    creatorBioText.textContent = yt.description || "No public description found on this channel profile.";

    // 2. Email Section
    renderEmailSection(emails);

    // 3. Instagram Section
    const igAccount = socials["instagram"];
    renderInstagramSection(igAccount);

    // 4. Other Socials
    renderOtherSocials(socials);

    // 5. Evidence Trail
    renderEvidenceTrail(evidence);

    // 6. Generate AI Outreach
    generateAIOutreach(yt);

    // 7. Check & Update Instagram Messaging Eligibility
    checkInstagramEligibility(igAccount ? igAccount.username : null, activeRecipientIgsid);

    // Reveal Workspace
    creatorWorkspace.style.display = "flex";
    creatorWorkspace.scrollIntoView({ behavior: "smooth", block: "start" });
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
  // 6. Instagram Section Rendering
  // ==========================================
  function renderInstagramSection(igAccount) {
    if (igAccount && igAccount.username) {
      currentDiscoveredUsername = igAccount.username.replace(/^@/, "");
      discoveredIgUsername.textContent = currentDiscoveredUsername;
      openIgLink.href = igAccount.url || `https://instagram.com/${currentDiscoveredUsername}`;
      igEvidenceText.textContent = `Discovered via ${igAccount.source} (${igAccount.confidence} Confidence)`;

      igDiscoveryPill.className = "pill-badge pill-success";
      igDiscoveryPill.innerHTML = `<i class="fa-solid fa-circle-check"></i> Identified`;

      igFoundView.style.display = "block";
      igNotFoundView.style.display = "none";

      consoleDiscoveryVal.textContent = `@${currentDiscoveredUsername}`;
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
  async function generateAIOutreach(yt) {
    outreachTextarea.value = "Generating personalized creator outreach message...";
    setRegenerateLoading(true);

    try {
      const payload = {
        creator_name: yt.channel_name,
        channel_name: yt.channel_name,
        platform: "YouTube",
        recent_video_title: yt.video_title,
        description_snippet: yt.description,
        sender_name: "Outreach Team"
      };

      const res = await fetch("/api/outreach/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        outreachTextarea.value = data.message || "";
        updateCharCount();

        // Render grounded evidence tags
        groundingEvidenceList.innerHTML = "";
        if (data.grounded_evidence && data.grounded_evidence.length > 0) {
          data.grounded_evidence.forEach(ev => {
            const span = document.createElement("span");
            span.className = "grounding-pill";
            span.innerHTML = `<i class="fa-solid fa-check"></i> ${ev}`;
            groundingEvidenceList.appendChild(span);
          });
        }
      } else {
        outreachTextarea.value = `Hi ${yt.channel_name || "there"},\n\nI really enjoyed your recent content on YouTube and wanted to connect about a potential collaboration.\n\nBest,\nOutreach Team`;
        updateCharCount();
      }
    } catch (e) {
      console.warn("AI Outreach error:", e);
      outreachTextarea.value = `Hi ${yt.channel_name || "there"},\n\nI really enjoyed your recent content on YouTube and wanted to connect about a potential collaboration.\n\nBest,\nOutreach Team`;
      updateCharCount();
    } finally {
      setRegenerateLoading(false);
    }
  }

  function setRegenerateLoading(isLoading) {
    regenerateOutreachBtn.disabled = isLoading;
    const btnText = regenerateOutreachBtn.querySelector(".btn-text");
    const icon = regenerateOutreachBtn.querySelector("i");
    if (icon) icon.className = isLoading ? "fa-solid fa-rotate fa-spin" : "fa-solid fa-rotate";
    if (btnText) btnText.textContent = isLoading ? "Generating..." : "Regenerate";
  }

  regenerateOutreachBtn.addEventListener("click", () => {
    if (currentExtraction && currentExtraction.youtube) {
      generateAIOutreach(currentExtraction.youtube);
    }
  });

  editOutreachBtn.addEventListener("click", () => {
    isEditingOutreach = !isEditingOutreach;
    if (isEditingOutreach) {
      outreachTextarea.focus();
      editBtnText.textContent = "Done";
      editOutreachBtn.classList.add("primary-mini-btn");
    } else {
      editBtnText.textContent = "Edit";
      editOutreachBtn.classList.remove("primary-mini-btn");
    }
  });

  copyOutreachBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(outreachTextarea.value);
    const span = copyOutreachBtn.querySelector("span");
    span.textContent = "Copied!";
    setTimeout(() => { span.textContent = "Copy"; }, 2000);
  });

  outreachTextarea.addEventListener("input", updateCharCount);

  function updateCharCount() {
    charCountVal.textContent = outreachTextarea.value.length;
    if (activeMessageType === "outreach") {
      activeDispatchTextarea.value = outreachTextarea.value;
    }
  }

  // ==========================================
  // 9. Instagram Eligibility & Messaging Console
  // ==========================================
  async function checkInstagramEligibility(username, user_id) {
    messagingEligibilityPill.className = "eligibility-status-pill pill-neutral";
    messagingEligibilityPill.innerHTML = `<span class="pill-dot"></span> Checking Eligibility...`;
    
    eligibilityBanner.className = "eligibility-banner info-mode";
    eligibilityBannerTitle.textContent = "Evaluating Meta Graph API Messaging Rules...";
    eligibilityBannerDesc.textContent = "Checking recipient identifier and Meta API configuration...";

    try {
      const res = await fetch("/api/social/instagram/eligibility", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          instagram_username: username,
          instagram_user_id: user_id
        })
      });

      if (res.ok) {
        const data = await res.json();
        currentEligibility = data;
        renderEligibilityUI(data);
      } else {
        renderEligibilityUI({
          configured: false,
          is_eligible: false,
          status: "failed",
          reason: "Unable to check Meta API eligibility."
        });
      }
    } catch (e) {
      renderEligibilityUI({
        configured: false,
        is_eligible: false,
        status: "failed",
        reason: `Eligibility check error: ${e.message}`
      });
    }
  }

  function renderEligibilityUI(data) {
    if (data.status === "eligible") {
      messagingEligibilityPill.className = "eligibility-status-pill eligible";
      messagingEligibilityPill.innerHTML = `<span class="pill-dot"></span> Eligible`;

      eligibilityBanner.className = "eligibility-banner eligible-mode";
      eligibilityBannerIcon.className = "fa-solid fa-circle-check banner-status-icon";
      eligibilityBannerTitle.textContent = "✓ Recipient Eligible for Official Meta API DM";
      eligibilityBannerDesc.textContent = data.reason;

      consoleRecipientVal.textContent = data.instagram_user_id ? `IGSID: ${data.instagram_user_id}` : `@${data.username}`;
      consoleRecipientVal.className = "console-meta-value highlight-ig";

      sendInstagramBtn.disabled = false;
      sendStatusDisplay.innerHTML = `<span style="color: #34d399;"><i class="fa-solid fa-check"></i> Ready to send real message via Meta API</span>`;

    } else if (data.status === "not_eligible") {
      messagingEligibilityPill.className = "eligibility-status-pill not_eligible";
      messagingEligibilityPill.innerHTML = `<span class="pill-dot"></span> Not Currently Eligible`;

      eligibilityBanner.className = "eligibility-banner ineligible-mode";
      eligibilityBannerIcon.className = "fa-solid fa-triangle-exclamation banner-status-icon";
      eligibilityBannerTitle.textContent = "✕ Recipient Not Eligible Under Meta API Rules";
      eligibilityBannerDesc.textContent = data.reason;

      consoleRecipientVal.textContent = data.username ? `@${data.username} (Requires IGSID)` : "No recipient";
      consoleRecipientVal.className = "console-meta-value text-muted";

      sendInstagramBtn.disabled = false; // Allow user to click and see exact Meta API validation
      sendStatusDisplay.innerHTML = `<span style="color: #fbbf24;"><i class="fa-solid fa-circle-info"></i> Official Meta API requires recipient IGSID</span>`;

    } else if (data.status === "not_configured") {
      messagingEligibilityPill.className = "eligibility-status-pill not_configured";
      messagingEligibilityPill.innerHTML = `<span class="pill-dot"></span> Meta API Not Configured`;

      eligibilityBanner.className = "eligibility-banner unconfigured-mode";
      eligibilityBannerIcon.className = "fa-solid fa-circle-xmark banner-status-icon";
      eligibilityBannerTitle.textContent = "Meta API Credentials Missing";
      eligibilityBannerDesc.textContent = data.reason;

      consoleRecipientVal.textContent = data.username ? `@${data.username}` : "Unconfigured";
      consoleRecipientVal.className = "console-meta-value text-muted";

      sendInstagramBtn.disabled = false;
      sendStatusDisplay.innerHTML = `<span style="color: #fb7185;"><i class="fa-solid fa-circle-exclamation"></i> Meta Access Token not configured</span>`;

    } else {
      messagingEligibilityPill.className = "eligibility-status-pill pill-neutral";
      messagingEligibilityPill.innerHTML = `<span class="pill-dot"></span> Not Discovered`;

      eligibilityBanner.className = "eligibility-banner info-mode";
      eligibilityBannerIcon.className = "fa-solid fa-circle-info banner-status-icon";
      eligibilityBannerTitle.textContent = "No Instagram Account Discovered";
      eligibilityBannerDesc.textContent = "An Instagram profile must be identified before messaging can be evaluated.";

      consoleRecipientVal.textContent = "None";
      sendInstagramBtn.disabled = true;
      sendStatusDisplay.textContent = "No Instagram recipient found";
    }
  }

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

  // Advanced Recipient IGSID Drawer Toggle
  toggleRecipientIdBtn.addEventListener("click", () => {
    const isHidden = recipientIdDrawer.style.display === "none";
    recipientIdDrawer.style.display = isHidden ? "block" : "none";
  });

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

  // ==========================================
  // 10. REAL Instagram Send Message Action
  // ==========================================
  sendInstagramBtn.addEventListener("click", async () => {
    const msgToSend = activeDispatchTextarea.value.trim();
    if (!msgToSend) {
      alert("Please provide a message text before sending.");
      return;
    }

    setSendingState(true);
    sendResultCard.style.display = "none";
    resultMetaInfo.style.display = "none";
    retrySendBtn.style.display = "none";

    const payload = {
      creator_id: currentExtraction?.youtube?.channel_id || null,
      instagram_username: currentDiscoveredUsername || null,
      instagram_user_id: activeRecipientIgsid || null,
      message: msgToSend,
      message_type: activeMessageType
    };

    try {
      const response = await fetch("/api/social/instagram/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const result = await response.json();
      setSendingState(false);
      renderSendResult(result);

    } catch (err) {
      setSendingState(false);
      renderSendResult({
        success: false,
        status: "failed",
        error: `Network error contacting server: ${err.message}`
      });
    }
  });

  function setSendingState(isSending) {
    sendInstagramBtn.disabled = isSending;
    const btnText = sendInstagramBtn.querySelector(".btn-text");
    const btnSpinner = sendInstagramBtn.querySelector(".btn-spinner");
    if (btnText) btnText.style.display = isSending ? "none" : "inline-flex";
    if (btnSpinner) btnSpinner.style.display = isSending ? "inline-flex" : "none";
    if (isSending) {
      sendStatusDisplay.innerHTML = `<span style="color: #818cf8;"><i class="fa-solid fa-circle-notch fa-spin"></i> Contacting official Meta Graph API...</span>`;
    }
  }

  function renderSendResult(res) {
    sendResultCard.style.display = "block";

    if (res.success && res.status === "sent") {
      sendResultCard.className = "send-result-card success-card";
      resultIcon.className = "fa-solid fa-circle-check result-card-icon";
      resultTitle.textContent = "✓ Test Message Sent Successfully";
      resultMessage.textContent = "Meta Graph API confirmed receipt and delivery of the message to the recipient.";
      
      resultMsgId.textContent = res.message_id || "N/A";
      resultTimestamp.textContent = res.sent_at ? new Date(res.sent_at).toLocaleTimeString() : new Date().toLocaleTimeString();
      resultMetaInfo.style.display = "flex";

      sendStatusDisplay.innerHTML = `<span style="color: #34d399; font-weight: 700;"><i class="fa-solid fa-check"></i> Message sent successfully</span>`;

    } else if (res.status === "not_eligible") {
      sendResultCard.className = "send-result-card ineligible-card";
      resultIcon.className = "fa-solid fa-triangle-exclamation result-card-icon";
      resultTitle.textContent = "✕ Recipient Not Eligible for Meta API Messaging";
      resultMessage.textContent = res.error || "The recipient is not eligible for this messaging flow under Meta API rules.";
      retrySendBtn.style.display = "inline-flex";

      sendStatusDisplay.innerHTML = `<span style="color: #fbbf24;"><i class="fa-solid fa-xmark"></i> Recipient not eligible</span>`;

    } else if (res.status === "not_configured") {
      sendResultCard.className = "send-result-card error-card";
      resultIcon.className = "fa-solid fa-circle-xmark result-card-icon";
      resultTitle.textContent = "✕ Meta Instagram API Not Configured";
      resultMessage.textContent = res.error || "Instagram messaging is not configured yet. Configure server credentials.";
      retrySendBtn.style.display = "none";

      sendStatusDisplay.innerHTML = `<span style="color: #fb7185;"><i class="fa-solid fa-xmark"></i> Meta API unconfigured</span>`;

    } else {
      sendResultCard.className = "send-result-card error-card";
      resultIcon.className = "fa-solid fa-circle-xmark result-card-icon";
      resultTitle.textContent = "✕ Message Could Not Be Sent";
      resultMessage.textContent = res.error || "Meta rejected the message or an internal error occurred.";
      retrySendBtn.style.display = "inline-flex";

      sendStatusDisplay.innerHTML = `<span style="color: #fb7185;"><i class="fa-solid fa-xmark"></i> Message dispatch failed</span>`;
    }

    sendResultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
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
      const statusPillClass = isSent ? "pill-success" : (rec.status === "not_eligible" ? "pill-warning" : "pill-danger");
      const statusLabel = isSent ? "Sent ✓" : (rec.status === "not_eligible" ? "Not Eligible" : "Failed");

      card.innerHTML = `
        <div class="history-item-header">
          <div>
            <strong>To: @${escapeHtml(rec.instagram_username || "unknown")}</strong>
            ${rec.instagram_user_id ? `<span style="font-size:11px; color: var(--text-muted);"> (ID: ${rec.instagram_user_id})</span>` : ""}
          </div>
          <span class="pill-badge ${statusPillClass}">${statusLabel}</span>
        </div>
        <div class="history-item-body">"${escapeHtml(rec.message)}"</div>
        <div class="history-item-meta">
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

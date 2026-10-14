/**
 * JobShield Chrome Extension — Webpage Job Extractor (content.js)
 *
 * Runs in the active webpage context when user clicks "Analyze Current Job".
 * Extracts job title, company, location, and description using:
 * 1. Schema.org JSON-LD structured data (standard on job boards)
 * 2. Site-specific selectors (LinkedIn, Indeed, Greenhouse, Lever, Workday, etc.)
 * 3. Semantic microdata & Open Graph metadata
 * 4. Content-density keyword heuristic fallback
 */
(() => {
  // Helper: clean text by trimming and normalizing whitespace
  function cleanText(text) {
    if (!text) return '';
    return text
      .replace(/\r\n/g, '\n')
      .replace(/\r/g, '\n')
      .replace(/\t/g, ' ')
      .replace(/[ \u00a0]+/g, ' ')
      .replace(/\n\s*\n\s*\n+/g, '\n\n')
      .trim();
  }

  // Helper: extract clean text from an HTML string or element
  function htmlToCleanText(htmlOrElement) {
    if (!htmlOrElement) return '';
    let container;
    if (typeof htmlOrElement === 'string') {
      try {
        if (typeof document !== 'undefined' && document.createElement) {
          container = document.createElement('div');
          container.innerHTML = htmlOrElement;
        } else {
          throw new Error('No DOM environment');
        }
      } catch {
        // Fallback for string HTML decoding without full DOM parser
        const textOnly = htmlOrElement
          .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
          .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
          .replace(/<(p|div|h[1-6]|li|tr|section|article|br)[^>]*>/gi, '\n')
          .replace(/<[^>]+>/g, ' ')
          .replace(/&amp;/g, '&')
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/&quot;/g, '"')
          .replace(/&#39;/g, "'");
        return cleanText(textOnly);
      }
    } else {
      try {
        container = htmlOrElement.cloneNode(true);
      } catch {
        container = htmlOrElement;
      }
    }

    // Remove non-content elements if container supports querySelectorAll
    if (container && container.querySelectorAll) {
      try {
        const unwanted = container.querySelectorAll(
          'script, style, noscript, nav, header, footer, svg, button, form, iframe, aside, select, input, textarea'
        );
        unwanted.forEach(el => el.remove && el.remove());

        // Insert line breaks after block elements
        const blockElements = container.querySelectorAll(
          'p, div, h1, h2, h3, h4, h5, h6, li, tr, blockquote, section, article'
        );
        blockElements.forEach(el => {
          if (el.insertAdjacentText) el.insertAdjacentText('afterend', '\n');
        });

        const breakElements = container.querySelectorAll('br');
        breakElements.forEach(el => {
          if (el.insertAdjacentText) el.insertAdjacentText('afterend', '\n');
        });
      } catch {
        // Use textContent directly
      }
    }

    return cleanText(container.innerText || container.textContent || '');
  }

  // --- STRATEGY 1: Schema.org JSON-LD ---
  function extractSchemaOrg() {
    try {
      const scripts = document.querySelectorAll('script[type="application/ld+json"]');
      for (const script of scripts) {
        if (!script.textContent) continue;
        let json;
        try {
          json = JSON.parse(script.textContent);
        } catch {
          continue;
        }

        const items = Array.isArray(json) ? json : (json['@graph'] ? json['@graph'] : [json]);
        for (const item of items) {
          if (!item) continue;
          const type = item['@type'];
          const isJob = Array.isArray(type) ? type.includes('JobPosting') : type === 'JobPosting';
          if (isJob) {
            const title = cleanText(item.title || item.name || '');
            let company = '';
            if (item.hiringOrganization) {
              company = typeof item.hiringOrganization === 'string'
                ? item.hiringOrganization
                : cleanText(item.hiringOrganization.name || '');
            }

            let location = '';
            if (item.jobLocation) {
              const loc = Array.isArray(item.jobLocation) ? item.jobLocation[0] : item.jobLocation;
              if (loc && loc.address) {
                const addr = loc.address;
                const parts = [addr.addressLocality, addr.addressRegion, addr.addressCountry].filter(Boolean);
                location = parts.join(', ');
              } else if (loc && loc.name) {
                location = cleanText(loc.name);
              }
            }

            let description = '';
            if (item.description) {
              description = htmlToCleanText(item.description);
            }

            if (description && description.length >= 40) {
              return {
                found: true,
                title,
                company,
                location,
                description,
                method: 'Schema.org JSON-LD'
              };
            }
          }
        }
      }
    } catch {
      // Fall through to next strategy
    }
    return { found: false };
  }

  // --- STRATEGY 2: Known Job Board & ATS Selectors ---
  function extractSiteSpecific() {
    const hostname = window.location.hostname.toLowerCase();

    const siteRules = [
      // Greenhouse
      {
        match: () => hostname.includes('greenhouse.io') || document.querySelector('#app_body, .app-title'),
        title: ['.app-title', '#header .title', 'h1.job-title'],
        company: ['.company-name', 'h2.company-name'],
        location: ['.location', '.body--metadata'],
        description: ['#content', '#app_body', '#main', '.content']
      },
      // Lever
      {
        match: () => hostname.includes('lever.co') || document.querySelector('.posting-headline'),
        title: ['.posting-headline h2', 'h2'],
        company: ['.main-header-text', '.main-header-logo-text'],
        location: ['.posting-categories .location', '.sort-by-time.posting-category'],
        description: ['.section-wrapper.page-full-width', '.posting-page', '[data-qa="job-description"]']
      },
      // LinkedIn
      {
        match: () => hostname.includes('linkedin.com'),
        title: [
          '.job-details-jobs-unified-top-card__job-title',
          '.jobs-unified-top-card__job-title',
          'h1.topcard__title',
          '.topcard__title',
          'h1'
        ],
        company: [
          '.job-details-jobs-unified-top-card__company-name',
          '.jobs-unified-top-card__company-name',
          '.topcard__flavor--black-link',
          '.topcard__org-name-link'
        ],
        location: [
          '.job-details-jobs-unified-top-card__bullet',
          '.jobs-unified-top-card__bullet',
          '.topcard__flavor:not(.topcard__flavor--black-link)'
        ],
        description: [
          '#job-details',
          '.jobs-description-content__text',
          '.show-more-less-html__markup',
          '.jobs-box__html-content',
          '.jobs-description__content'
        ]
      },
      // Indeed
      {
        match: () => hostname.includes('indeed.com'),
        title: [
          'h1.jobsearch-JobInfoHeader-title',
          '[data-testid="jobsearch-JobInfoHeader-title"]',
          'h2.jobTitle',
          'h1'
        ],
        company: [
          '[data-testid="inlineHeader-companyName"]',
          '.jobsearch-CompanyInfoContainer a',
          '[data-company-name="true"]'
        ],
        location: [
          '[data-testid="inlineHeader-companyLocation"]',
          '[data-testid="job-location"]'
        ],
        description: [
          '#jobDescriptionText',
          '.jobsearch-jobDescriptionText'
        ]
      },
      // Workday
      {
        match: () => hostname.includes('myworkdayjobs.com') || document.querySelector('[data-automation-id="jobPostingHeader"]'),
        title: ['[data-automation-id="jobPostingHeader"]'],
        company: ['[data-automation-id="jobPostingSubHeader"]'],
        location: ['[data-automation-id="jobPostingLocation"]'],
        description: ['[data-automation-id="jobPostingDescription"]']
      },
      // Ashby
      {
        match: () => hostname.includes('ashbyhq.com'),
        title: ['h1'],
        company: ['header span', 'nav a'],
        location: ['header [class*="location"]'],
        description: ['[class*="jobDescription"]', '.ashby-job-posting-description']
      },
      // Glassdoor
      {
        match: () => hostname.includes('glassdoor.com'),
        title: ['[data-test="job-title"]', '.css-1vg6q84'],
        company: ['[data-test="employer-name"]'],
        location: ['[data-test="location"]'],
        description: ['[data-test="job-description-text"]', '#JobDescriptionContainer']
      },
      // ZipRecruiter
      {
        match: () => hostname.includes('ziprecruiter.com'),
        title: ['h1.job_title', 'h1'],
        company: ['.hiring_company_text'],
        location: ['.location_text'],
        description: ['.jobDescriptionSection', '.job_description']
      }
    ];

    function pickFirst(selectors) {
      if (!selectors) return '';
      for (const sel of selectors) {
        try {
          const el = document.querySelector(sel);
          if (el) {
            const txt = cleanText(el.innerText || el.textContent || '');
            if (txt) return txt;
          }
        } catch {}
      }
      return '';
    }

    function pickFirstDescription(selectors) {
      if (!selectors) return '';
      for (const sel of selectors) {
        try {
          const el = document.querySelector(sel);
          if (el) {
            const txt = htmlToCleanText(el);
            if (txt && txt.length >= 40) return txt;
          }
        } catch {}
      }
      return '';
    }

    for (const rule of siteRules) {
      if (rule.match()) {
        const desc = pickFirstDescription(rule.description);
        if (desc) {
          const title = pickFirst(rule.title);
          const company = pickFirst(rule.company);
          const location = pickFirst(rule.location);
          return {
            found: true,
            title,
            company,
            location,
            description: desc,
            method: 'Site-Specific Selector'
          };
        }
      }
    }

    return { found: false };
  }

  // --- STRATEGY 3: Semantic HTML & Microdata ---
  function extractSemantic() {
    function pickFirst(selectors) {
      for (const sel of selectors) {
        try {
          const el = document.querySelector(sel);
          if (el) {
            const txt = cleanText(el.innerText || el.textContent || '');
            if (txt) return txt;
          }
        } catch {}
      }
      return '';
    }

    const title = pickFirst([
      '[itemprop="title"]',
      'meta[property="og:title"]',
      'h1[class*="job"]',
      'h1[class*="title"]',
      'h1'
    ]);

    const company = pickFirst([
      '[itemprop="hiringOrganization"]',
      '[class*="company-name"]',
      '[class*="companyName"]',
      '[class*="employer"]',
      'meta[property="og:site_name"]'
    ]);

    const location = pickFirst([
      '[itemprop="jobLocation"]',
      '[class*="job-location"]',
      '[class*="location"]'
    ]);

    const descSelectors = [
      '[itemprop="description"]',
      '[class*="job-description"]',
      '[class*="jobDescription"]',
      '[class*="job_description"]',
      '[class*="posting-description"]',
      '[id*="job-description"]',
      '[id*="jobDescription"]',
      '[id*="job_description"]',
      'article[class*="job"]',
      'main [class*="description"]'
    ];

    for (const sel of descSelectors) {
      try {
        const el = document.querySelector(sel);
        if (el) {
          const text = htmlToCleanText(el);
          if (text && text.length >= 50) {
            return {
              found: true,
              title,
              company,
              location,
              description: text,
              method: 'Semantic Selectors'
            };
          }
        }
      } catch {}
    }

    return { found: false, title, company, location };
  }

  // --- STRATEGY 4: Keyword & Content-Density Heuristic Fallback ---
  function extractHeuristicFallback(partialMeta) {
    const jobKeywords = [
      'responsibilities',
      'requirements',
      'qualifications',
      'about the role',
      'about this role',
      'what you will do',
      "what you'll do",
      'who you are',
      'benefits',
      'skills required',
      'job summary',
      'experience required',
      'duties'
    ];

    const candidates = document.querySelectorAll('article, main, [role="main"], section, div');
    let maxKeywordMatches = 0;
    let bestText = '';

    for (const candidate of candidates) {
      if (candidate === document.body || candidate === document.documentElement) continue;

      const rawText = candidate.innerText || candidate.textContent || '';
      if (rawText.length < 100 || rawText.length > 50000) continue;

      const lower = rawText.toLowerCase();
      let matchCount = 0;
      for (const kw of jobKeywords) {
        if (lower.includes(kw)) {
          matchCount++;
        }
      }

      if (matchCount > maxKeywordMatches) {
        const cleaned = htmlToCleanText(candidate);
        if (cleaned.length >= 80) {
          maxKeywordMatches = matchCount;
          bestText = cleaned;
        }
      }
    }

    if (maxKeywordMatches >= 2 && bestText) {
      const h1 = document.querySelector('h1');
      const title = partialMeta.title || (h1 ? cleanText(h1.innerText || h1.textContent || '') : '');
      return {
        found: true,
        title,
        company: partialMeta.company || '',
        location: partialMeta.location || '',
        description: bestText,
        method: 'Content-Density Fallback'
      };
    }

    return { found: false };
  }

  // --- MAIN EXTRACTION DISPATCHER ---
  function extractJob() {
    // 1. Try Schema.org JSON-LD
    const s1 = extractSchemaOrg();
    if (s1.found) return formatResult(s1);

    // 2. Try Site-Specific / ATS Selectors
    const s2 = extractSiteSpecific();
    if (s2.found) return formatResult(s2);

    // 3. Try Semantic HTML & Microdata
    const s3 = extractSemantic();
    if (s3.found) return formatResult(s3);

    // 4. Try Content-Density Keyword Fallback
    const s4 = extractHeuristicFallback(s3);
    if (s4.found) return formatResult(s4);

    return {
      success: false,
      error: 'no_job_found',
      message: "We couldn't automatically find a job description on this page. Try selecting a supported job listing or paste the job text manually."
    };
  }

  function formatResult(extracted) {
    const title = extracted.title || '';
    const company = extracted.company || '';
    const location = extracted.location || '';
    const description = extracted.description || '';

    // Format clean composite text suitable for review and JobShield prediction
    let headerLines = [];
    if (title && company) {
      headerLines.push(`${title} — ${company}`);
    } else if (title) {
      headerLines.push(title);
    } else if (company) {
      headerLines.push(company);
    }

    if (location) {
      headerLines.push(`Location: ${location}`);
    }

    const headerBlock = headerLines.length > 0 ? headerLines.join('\n') + '\n\n' : '';
    const fullText = (headerBlock + description).trim();

    return {
      success: true,
      jobTitle: title,
      company: company,
      location: location,
      description: description,
      fullText: fullText,
      method: extracted.method || 'Auto-detection',
      charCount: fullText.length,
      url: window.location.href
    };
  }

  return extractJob();
})();

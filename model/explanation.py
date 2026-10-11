import re
import html
from model.predictor import model, tfidf, clean_text_single

def get_strength_label(weight):
    abs_val = abs(weight)
    if abs_val > 1.5:
        return "Strong"
    elif abs_val > 0.7:
        return "Moderate"
    else:
        return "Weak"

def get_flagged_reasons(raw_text, top_n=5):
    """
    Identifies which words in the user's input most contributed
    to the fraud/genuine prediction, using LR's learned coefficients.
    Returns lists of tuples: (word, strength, weight)
    """
    cleaned = clean_text_single(raw_text)
    words_in_text = set(cleaned.split())

    feature_names = list(tfidf.get_feature_names_out())
    word_to_idx = {word: idx for idx, word in enumerate(feature_names)}

    lr_component = model.named_estimators_['lr']
    coefficients = lr_component.coef_[0][:len(feature_names)]

    word_weights = {}
    for word in words_in_text:
        if word in word_to_idx:
            idx = word_to_idx[word]
            word_weights[word] = coefficients[idx]

    sorted_words = sorted(word_weights.items(), key=lambda x: x[1], reverse=True)

    fraud_reasons = [(w, get_strength_label(weight), weight) for w, weight in sorted_words if weight > 0][:top_n]

    genuine_sorted = sorted([(w, weight) for w, weight in word_weights.items() if weight < 0], key=lambda x: x[1])
    genuine_reasons = [(w, get_strength_label(weight), weight) for w, weight in genuine_sorted][:top_n]

    return fraud_reasons, genuine_reasons

def get_structured_feature_contributions(telecommuting, has_company_logo, has_questions, has_salary_range):
    """
    Extracts LR coefficients for the 4 structured features and determines
    the contribution direction for features checked/True by the user.
    """
    lr_component = model.named_estimators_['lr']
    struct_coefs = lr_component.coef_[0][-4:]

    features = [
        ("Remote / Work from home option", "the remote work option", telecommuting, struct_coefs[0]),
        ("Company logo/profile present", "the company logo/profile", has_company_logo, struct_coefs[1]),
        ("Screening questions included", "screening questions", has_questions, struct_coefs[2]),
        ("Salary range mentioned", "the salary range", has_salary_range, struct_coefs[3]),
    ]

    contributions = []
    for display_name, summary_name, is_checked, coef in features:
        if is_checked:
            direction = "fraud" if coef > 0 else "genuine"
            contributions.append({
                "display_name": display_name,
                "summary_name": summary_name,
                "direction": direction,
                "coef": coef,
                "strength": get_strength_label(coef)
            })
    return contributions

def generate_plain_language_summary(result_label, fraud_reasons, genuine_reasons, structured_contributions):
    # Determine top words (2 to 3) based on prediction
    if result_label in ["LIKELY FRAUDULENT", "UNCERTAIN — REVIEW RECOMMENDED"]:
        top_words = [w for w, s, c in fraud_reasons[:3]]
        if not top_words and genuine_reasons:
            top_words = [w for w, s, c in genuine_reasons[:3]]
    else:
        top_words = [w for w, s, c in genuine_reasons[:3]]
        if not top_words and fraud_reasons:
            top_words = [w for w, s, c in fraud_reasons[:3]]

    # Format words string
    if len(top_words) == 1:
        words_str = f"'{top_words[0]}'"
    elif len(top_words) == 2:
        words_str = f"'{top_words[0]}' and '{top_words[1]}'"
    elif len(top_words) >= 3:
        words_str = f"'{top_words[0]}', '{top_words[1]}', and '{top_words[2]}'"
    else:
        words_str = ""

    # Group structured feature contributions
    fraud_structs = [c["summary_name"] for c in structured_contributions if c["direction"] == "fraud"]
    genuine_structs = [c["summary_name"] for c in structured_contributions if c["direction"] == "genuine"]

    def join_items(items):
        if len(items) == 1:
            return items[0]
        elif len(items) == 2:
            return f"{items[0]} and {items[1]}"
        else:
            return f"{', '.join(items[:-1])}, and {items[-1]}"

    fraud_struct_str = join_items(fraud_structs) if fraud_structs else ""
    genuine_struct_str = join_items(genuine_structs) if genuine_structs else ""

    # Build single sentence summary
    if result_label in ["LIKELY FRAUDULENT", "UNCERTAIN — REVIEW RECOMMENDED"]:
        if words_str and (fraud_struct_str or genuine_struct_str):
            if fraud_struct_str and genuine_struct_str:
                sentence = (f"This job posting was flagged as suspicious primarily due to keywords like {words_str}, "
                            f"with {fraud_struct_str} adding to the risk while {genuine_struct_str} provided a positive signal.")
            elif fraud_struct_str:
                sentence = (f"This job posting was flagged as suspicious primarily due to keywords like {words_str}, "
                            f"along with {fraud_struct_str} which also contributed to the risk.")
            else:
                sentence = (f"This job posting was flagged as suspicious primarily due to keywords like {words_str}, "
                            f"though {genuine_struct_str} provided a positive signal.")
        elif words_str:
            sentence = f"This job posting was flagged as suspicious primarily due to keywords like {words_str}."
        elif fraud_struct_str or genuine_struct_str:
            if fraud_struct_str:
                sentence = f"This job posting was flagged as suspicious based on job details like {fraud_struct_str}."
            else:
                sentence = f"This job posting was flagged as suspicious based on overall text patterns, despite positive signals from {genuine_struct_str}."
        else:
            sentence = "This job posting was flagged as suspicious based on overall language patterns in the text."
    else:
        # LIKELY GENUINE
        if words_str and (genuine_struct_str or fraud_struct_str):
            if genuine_struct_str and fraud_struct_str:
                sentence = (f"This job posting appears genuine primarily due to reassuring terms like {words_str}, "
                            f"supported by positive signals from {genuine_struct_str}, despite {fraud_struct_str} raising slight risk.")
            elif genuine_struct_str:
                sentence = (f"This job posting appears genuine primarily due to reassuring terms like {words_str}, "
                            f"supported by positive signals from {genuine_struct_str}.")
            else:
                sentence = (f"This job posting appears genuine primarily due to reassuring terms like {words_str}, "
                            f"despite {fraud_struct_str} raising slight risk.")
        elif words_str:
            sentence = f"This job posting appears genuine primarily due to reassuring terms like {words_str}."
        elif genuine_struct_str or fraud_struct_str:
            if genuine_struct_str:
                sentence = f"This job posting appears genuine based on positive signals from job details like {genuine_struct_str}."
            else:
                sentence = f"This job posting appears genuine based on text analysis, despite {fraud_struct_str} raising slight risk."
        else:
            sentence = "This job posting appears genuine based on overall text patterns."

    return sentence

def highlight_flagged_text(raw_text, fraud_reasons, genuine_reasons, theme_name="dark"):
    fraud_words = set(w.lower() for w, s, c in fraud_reasons)
    genuine_words = set(w.lower() for w, s, c in genuine_reasons)

    escaped_text = html.escape(raw_text)

    if theme_name == "light":
        fraud_bg = "#fee2e2"
        fraud_fg = "#991b1b"
        genuine_bg = "#dcfce7"
        genuine_fg = "#166534"
        container_bg = "#F8F9FC"
        container_border = "#DDE2EF"
        container_text = "#20283B"
    else:
        fraud_bg = "#5c2b2b"
        fraud_fg = "#ff6b6b"
        genuine_bg = "#2b5c3a"
        genuine_fg = "#51cf66"
        container_bg = "#1D2231"
        container_border = "#343B50"
        container_text = "#E8ECF5"

    def replace_word(match):
        word = match.group(0)
        word_lower = word.lower()
        if word_lower in fraud_words:
            return f'<span style="background-color: {fraud_bg}; color: {fraud_fg}; padding: 2px 6px; border-radius: 4px; font-weight: bold;">{word}</span>'
        elif word_lower in genuine_words:
            return f'<span style="background-color: {genuine_bg}; color: {genuine_fg}; padding: 2px 6px; border-radius: 4px; font-weight: bold;">{word}</span>'
        return word

    highlighted = re.sub(r'\b[A-Za-z]+\b', replace_word, escaped_text)

    html_container = (
        f'<div style="white-space: pre-wrap; font-family: sans-serif; font-size: 15px; '
        f'line-height: 1.8; color: {container_text}; background-color: {container_bg}; '
        f'border: 1px solid {container_border}; padding: 18px; border-radius: 10px; '
        f'margin-bottom: 16px; margin-top: 8px;">{highlighted}</div>'
    )
    return html_container

"""
Resume Parser
Extract text and parse information from resumes
"""
import re
import os
from typing import Dict, List, Optional


def extract_text(file_path: str) -> str:
    """
    Extract text from document

    Args:
        file_path: Path to document file

    Returns:
        Extracted text
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.pdf':
        return extract_from_pdf(file_path)
    elif ext in ['.doc', '.docx']:
        return extract_from_docx(file_path)
    elif ext == '.txt':
        return extract_from_txt(file_path)
    elif ext == '.rtf':
        return extract_from_rtf(file_path)
    else:
        raise ValueError(f'Unsupported file type: {ext}')


def extract_from_pdf(file_path: str) -> str:
    """Extract text from PDF"""
    try:
        import pdfplumber
        text = ''
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
        return text
    except Exception as e:
        # Fallback to PyPDF2
        try:
            import PyPDF2
            text = ''
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + '\n'
            return text
        except:
            raise Exception(f"PDF extraction failed: {str(e)}")


def extract_from_docx(file_path: str) -> str:
    """Extract text from DOCX"""
    try:
        from docx import Document
        doc = Document(file_path)
        return '\n'.join([para.text for para in doc.paragraphs])
    except Exception as e:
        raise Exception(f"DOCX extraction failed: {str(e)}")


def extract_from_txt(file_path: str) -> str:
    """Extract text from TXT"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        # Try different encoding
        with open(file_path, 'r', encoding='latin-1') as file:
            return file.read()


def extract_from_rtf(file_path: str) -> str:
    """Extract text from RTF (basic)"""
    # Simple RTF text extraction (strips formatting)
    with open(file_path, 'r', encoding='latin-1') as file:
        content = file.read()

    # Remove RTF control words
    text = re.sub(r'\\[a-z]+\d*\s?', '', content)
    text = re.sub(r'[{}]', '', text)

    return text.strip()


def parse_resume(text: str) -> Dict:
    """
    Parse resume text to extract structured information

    Args:
        text: Resume text

    Returns:
        Dictionary with parsed fields
    """
    data = {
        'name': extract_name(text),
        'email': extract_email(text),
        'phones': extract_phones(text),
        'skills': extract_skills(text),
        'education': extract_education(text),
        'experience': extract_experience(text),
    }

    return data


def extract_name(text: str) -> Optional[str]:
    """Extract name from resume"""
    lines = text.strip().split('\n')

    # Name is usually in first few lines
    for line in lines[:5]:
        line = line.strip()

        # Skip empty lines and email/phone lines
        if not line or '@' in line or re.search(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', line):
            continue

        # Name pattern: 2-3 words, capitalized
        if re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+(\s+[A-Z][a-z]+)?$', line):
            return line

    return None


def extract_email(text: str) -> Optional[str]:
    """Extract email address"""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_phones(text: str) -> List[str]:
    """Extract phone numbers"""
    # US phone patterns
    patterns = [
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890 or 123-456-7890
        r'\d{3}[-.\s]\d{4}',  # 123-4567
    ]

    phones = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        phones.extend(matches)

    return list(set(phones))[:3]  # Return up to 3 unique phones


def extract_skills(text: str) -> List[str]:
    """Extract skills from resume"""
    # Common skill keywords
    common_skills = [
        # Programming languages
        'Python', 'Java', 'JavaScript', 'C++', 'C#', 'Ruby', 'PHP', 'Swift', 'Go', 'Rust',
        'TypeScript', 'Kotlin', 'Scala', 'R', 'MATLAB', 'Perl', 'Shell', 'PowerShell',

        # Web technologies
        'HTML', 'CSS', 'React', 'Angular', 'Vue.js', 'Node.js', 'Express', 'Django',
        'Flask', 'Spring', 'ASP.NET', 'jQuery', 'Bootstrap', 'Tailwind',

        # Databases
        'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite', 'Oracle', 'SQL Server',
        'Cassandra', 'DynamoDB', 'Elasticsearch',

        # Cloud & DevOps
        'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'GitLab', 'CircleCI',
        'Terraform', 'Ansible', 'Chef', 'Puppet',

        # Tools & Platforms
        'Git', 'GitHub', 'Jira', 'Confluence', 'Slack', 'VS Code', 'IntelliJ',

        # Methodologies
        'Agile', 'Scrum', 'DevOps', 'CI/CD', 'TDD', 'BDD',

        # Soft skills
        'Leadership', 'Communication', 'Problem Solving', 'Team Player', 'Management',
    ]

    found_skills = []

    # Case-insensitive search
    text_lower = text.lower()
    for skill in common_skills:
        if skill.lower() in text_lower:
            found_skills.append(skill)

    return found_skills


def extract_education(text: str) -> List[Dict]:
    """Extract education information"""
    education = []

    # Degree patterns
    degree_patterns = [
        r"(?:Bachelor|Master|Ph\.?D|Associate|B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?)[\w\s.,]*",
    ]

    for pattern in degree_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            education.append({
                'degree': match.group(0).strip()
            })

    return education[:3]  # Return up to 3 degrees


def extract_experience(text: str) -> List[Dict]:
    """Extract work experience (basic)"""
    experience = []

    # Look for years patterns like "2018-2020" or "2018-Present"
    year_patterns = r'\b(20\d{2})\s*[-–]\s*(20\d{2}|Present|Current)\b'

    matches = re.finditer(year_patterns, text, re.IGNORECASE)
    for match in matches:
        experience.append({
            'period': match.group(0),
            'start_year': match.group(1),
            'end_year': match.group(2)
        })

    return experience[:5]  # Return up to 5 experiences

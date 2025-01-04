import platform, os, re

def clear_console():
    """Clear the console screen."""
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

def link_to_id(link):
    """Extract file or folder ID from a Google Drive link."""
    id_pattern = r"drive\.google\.com\/(?:file\/d\/|drive\/(?:u\/\d+\/)?folders\/|open\?id=)([-\w]+)"
    match = re.search(id_pattern, link)
    if match:
        folder_id = match.group(1)
        print(f"Extracted ID: {folder_id} from link: {link}")
        return folder_id
    else:
        raise ValueError(f"Unable to extract ID from link: {link}")

def sanitizer_names(filename):
    """Sanitize filenames to avoid invalid characters."""
    filename = re.sub(r"[<>:\"/|?*\'\x00-\x1F]", '_', filename).strip()
    return filename

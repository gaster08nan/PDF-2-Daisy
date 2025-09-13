

def read_txt_file(file_path):
    """
    Description: Read a text file and return a list of lines.
    Input:
        file_path: str, the path to the text file.
    Return:
        lines: list, a list of lines.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    return lines

def ms_to_anemone_time(ms: int) -> str:
    """
    Description: Convert milliseconds to Anemone JSON time format M:SS.FF
    Input:
        ms: int, the number of milliseconds.
    Return:
        time: str, the time in Anemone JSON time format M:SS.FF
    """
    total_seconds = ms / 1000.0
    minutes = int(total_seconds // 60)
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:05.2f}"  # e.g. "63:15.20"
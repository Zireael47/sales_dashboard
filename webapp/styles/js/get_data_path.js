function get_data_path(data) {
    if (data.name) {
        return data.name.split("|");
    } else {
        return '';
    }
}
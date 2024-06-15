function color_values(params){
    if (params.value == '0') {
        return {
            'color': 'black',
            'font-weight': 'bold'
        }
    }
    if (params.value < '0') {
        return{
            'color': 'red',
            'font-weight': 'bold'
        }
    }
    if (params.value > '0') {
        return{
            'color': 'MediumSeaGreen',
            'font-weight': 'bold'
        }
    }
}
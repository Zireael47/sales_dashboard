const root = parent.document.querySelector('.stApp');
let lastBackgroundColor = null;
function updateContainerBackground(currentBackground) {
    parent.document.documentElement.style.setProperty(
        '--background-color', currentBackground
    );
    ;
}
function checkForBackgroundColorChange() {
    const style = window.getComputedStyle(root);
    const currentBackgroundColor = style.backgroundColor;
    if (currentBackgroundColor !== lastBackgroundColor) {
        lastBackgroundColor = currentBackgroundColor;
        updateContainerBackground(lastBackgroundColor);
    }
}
const observerCallback = (mutationsList, observer) => {
    for(let mutation of mutationsList) {
        if (
            mutation.type === 'attributes' &&
            (
                mutation.attributeName === 'class' ||
                mutation.attributeName === 'style'
            )
        )
        {
            checkForBackgroundColorChange();
        }
    }
};
const main = () => {
    checkForBackgroundColorChange();
    const observer = new MutationObserver(observerCallback);
    observer.observe(
        root, { attributes: true, childList: false, subtree: false }
    );
}
// main();
document.addEventListener("DOMContentLoaded", main);
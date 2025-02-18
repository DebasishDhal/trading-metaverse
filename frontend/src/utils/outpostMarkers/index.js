const images = {};

function importAll(r) {
  r.keys().forEach((key) => {
    images[key.replace('./', '').replace(/\.[^/.]+$/, "")] = r(key);
  });
}

importAll(require.context('./', false, /\.(png|jpe?g|svg|gif)$/));

export default images;
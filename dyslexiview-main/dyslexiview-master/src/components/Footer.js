import { useState } from "react";
import { Container, Row, Col, Tab, Nav } from "react-bootstrap";
import './Footer.css';

export const Footer = ({ onFileSelected }) => {
  const [file, setFile] = useState();
  const [originalText, setOriginalText] = useState('');
  const [audioUrl, setAudioUrl] = useState('');
  const [error, setError] = useState('');

  function handleChange(e) {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('image', selectedFile);

    setFile(URL.createObjectURL(selectedFile));

    fetch('http://localhost:5000/', {
      method: 'POST',
      body: formData
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          setOriginalText(data.original_text);
          setAudioUrl(`http://localhost:5000/${data.original_sound}`);
          setError('');
        } else {
          setOriginalText('');
          setAudioUrl('');
          setError('Error: ' + (data.error || 'Unknown error'));
        }
      })
      .catch(error => {
        console.error('Error:', error);
        setError('Error: Network error');
        setOriginalText('');
        setAudioUrl('');
      });
  }

  return (
    <div className="footer">
      <Container>
        <Row>
          <Col>
            <div className="upload-section">
              <input
                type="file"
                accept="image/*"
                onChange={handleChange}
                className="new-email-bx-button"
              />
            </div>

            {file && (
              <div className="image-preview">
                <h4>Image sélectionnée :</h4>
                <img src={file} alt="Selected" style={{ maxWidth: '300px' }} />
              </div>
            )}

            {originalText && (
              <div className="dyslexic-text-section">
                <h4>Texte extrait :</h4>
                <div className="dyslexic-text-container fade-in">
                  {originalText.split(' ').map((word, index) => (
                    <span key={index} className="word-container">
                      {word.length > 3 ? (
                        <>
                          {Array.from({ length: Math.ceil(word.length / 3) }, (_, i) => (
                            <span 
                              key={i} 
                              className={`syllable syllable-${i % 2}`}
                            >
                              {word.slice(i * 3, (i + 1) * 3)}
                            </span>
                          ))}
                        </>
                      ) : (
                        <span className="syllable">{word}</span>
                      )}
                      {' '}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {audioUrl && (
              <div className="audio-section">
                <h4>Audio :</h4>
                <audio controls src={audioUrl}>
                  Votre navigateur ne supporte pas l'élément audio.
                </audio>
              </div>
            )}

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}
          </Col>
        </Row>
      </Container>
    </div>
  );
}

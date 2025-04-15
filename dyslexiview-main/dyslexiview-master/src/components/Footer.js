import { useState } from "react";
import { Container, Row, Col, Tab, Nav } from "react-bootstrap";
import AudioPlayer from '../AudioPlayer.js';
import AudioPlayer2 from '../AudioPlayer2.js';
import AudioRecorder from './AudioRecorder';
import RecordingsList from './RecordingsList';

export const Footer = ({ onFileSelected }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [activeTab, setActiveTab] = useState('upload');
  const [file, setFile] = useState();
  const [message, setMessage] = useState('');
  const [originalText, setOriginalText] = useState('');
  const [originalSound, setOriginalSound] = useState('');
  const [summarizedText, setSummarizedText] = useState('');
  const [summarizedSound, setSummarizedSound] = useState('');
  const [error, setError] = useState('');

  function handleChange(e) {
    const selectedFile = e.target.files[0];
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
          setOriginalSound(data.original_sound);
          setSummarizedText(data.summarized_text);
          setSummarizedSound(data.summary_sound);
          setError('');
        } else {
          setOriginalText('');
          setOriginalSound('');
          setSummarizedText('');
          setSummarizedSound('');
          setError('Error: ' + (data.error || 'Unknown error'));
        }
      })
      .catch(error => {
        console.error('Error:', error);
        setError('Error: Network error');
        setOriginalText('');
        setOriginalSound('');
        setSummarizedText('');
        setSummarizedSound('');
      });
  }

  const handleRecordingComplete = (data) => {
    console.log('Recording completed:', data);
  };

  return (
    <footer className="footer" id="footer">
      <Container>
        <Row>
          <Col lg={12}>
            <div className="newsletter-bx wow slideInUp">
              <Tab.Container activeKey={activeTab} onSelect={(k) => setActiveTab(k)}>
                <Row>
                  <Col lg={12}>
                    <Nav variant="pills" className="nav-tabs mb-4">
                      <Nav.Item>
                        <Nav.Link eventKey="upload">Upload Image</Nav.Link>
                      </Nav.Item>
                      <Nav.Item>
                        <Nav.Link eventKey="record">Record Audio</Nav.Link>
                      </Nav.Item>
                    </Nav>
                  </Col>
                </Row>

                <Tab.Content>
                  <Tab.Pane eventKey="upload">
                    <Row>
                      <Col lg={12} md={6} xl={5}>
                        <h3>Provide your textual input<br />Or upload a file!</h3>
                      </Col>
                      <Col md={6} xl={7}>
                        <form>
                          <div className="new-email-bx">
                            <input type="file" onChange={handleChange} className="new-email-bx-button" />
                          </div>
                        </form>
                      </Col>
                    </Row>
                    <Row>
                      <Col>
                        {file && <h4><b><u>Selected Image:</u></b></h4>}
                        {file && <img src={file} alt="Selected" style={{ width: '300px' }} />}
                      </Col>
                      <Col size={50}>
                        {originalText && <h4><b><u>Extracted Text:</u></b></h4>}
                        {originalText && <h5>{originalText}</h5>}
                        {summarizedText && <h4><b><u>Summarized Text:</u></b></h4>}
                        {summarizedText && <h5>{summarizedText}</h5>}
                      </Col>
                      <Row>
                        <Col>
                          {summarizedSound && (
                            <div>
                              <h4><b><u>Summarized Sound:</u></b></h4>
                              <AudioPlayer />
                            </div>
                          )}
                        </Col>
                        <Col>
                          {originalSound && (
                            <div>
                              <h4><b><u>Original Sound:</u></b></h4>
                              <AudioPlayer2 />
                            </div>
                          )}
                        </Col>
                      </Row>
                    </Row>
                  </Tab.Pane>

                  <Tab.Pane eventKey="record">
                    <Row>
                      <Col lg={12}>
                        <h3>Record and Enhance Audio</h3>
                        <p>Record your voice and let us enhance it for better clarity!</p>
                        <AudioRecorder onRecordingComplete={handleRecordingComplete} />
                        <RecordingsList />
                      </Col>
                    </Row>
                  </Tab.Pane>
                </Tab.Content>
              </Tab.Container>
            </div>
          </Col>
        </Row>
      </Container>
    </footer>
  )
}

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import EmailInput from './pages/EmailInput';
import EmailList from './pages/EmailList';
import Chat from './pages/Chat';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<EmailInput />} />
          <Route path="/emails" element={<EmailList />} />
          <Route path="/chat" element={<Chat />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;

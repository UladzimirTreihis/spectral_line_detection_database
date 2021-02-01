import axios from 'axios';
import './App.css';
// import { useEffect, useState } from 'react';
import Navbar from './components/navbar/Navbar';
import Form from './components/form/Form';

function App() {

  return (
    <div className="App">
      <Navbar />
      <Form />
    </div>
  );
}

export default App;

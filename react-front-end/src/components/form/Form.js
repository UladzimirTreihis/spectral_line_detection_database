import React, { useState, useEffect } from 'react';
import { makeStyles } from '@material-ui/core/styles';
import TextField from '@material-ui/core/TextField';
import Grid from '@material-ui/core/Grid';

const useStyles = makeStyles((theme) => ({
  root: {
    '& .MuiTextField-root': {
      margin: theme.spacing(1),
      width: '80%',
      position: 'relative',
    },
  },
}));

const Form = () => {
  const classes = useStyles();
  const initialFValues = {
    name : '',
    institution: '',
    password: '',
    Email: '',
  };

  const [values, setValues] = useState(initialFValues)

  return (
    <form className={classes.root} noValidate autoComplete="off">
      <Grid container>
        <Grid item xs={6}>
        <TextField 
        variant = "outlined"
        label = "Full Name"
        value = {values.name}
        />
        <TextField 
        variant = "outlined"
        label = "Institution"
        value = {values.institution}
        />
        <TextField 
        variant = "outlined"
        label = "Password"
        value = {values.password}
        />
        <TextField 
        variant = "outlined"
        label = "Confirm Password"
        />
        <TextField 
        variant = "outlined"
        label = "E-mail"
        value = {values.email}
        />
        </Grid>
      </Grid>
    </form>
  );
}

export default Form;
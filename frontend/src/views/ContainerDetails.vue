<template>
  <div class="container-details">
    <top-bar title="Container Details"></top-bar>
  </div>
</template>
<script lang="ts">
import Vue from 'vue';
import { Container } from '../store/models';

interface State {
  container: Container;
}

export default Vue.extend({
  name: 'ContainerDetails',
  mounted() {
    this.loadContainer();
  },
  data: (): { localState: State } => ({
    localState: {
      container: null,
    }
  }),
  methods: {
    loadContainer() {
      this.$store.dispatch('containers/get', { entity: this.$route.params.entity, collection: this.$route.params.collection, container: this.$route.params.container })
        .then((container: Container) => {
          this.localState.container = container;
        })
        .catch(err => this.$store.commit('snackbar/showError', err))
    }
  }
});
</script>